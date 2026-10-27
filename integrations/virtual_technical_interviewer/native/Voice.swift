import Foundation
import AVFoundation
import Speech
import AppKit
import CoreFoundation
import CryptoKit

// Local presentation/input accessory only. The existing native provider and
// Python controller retain all request, turn, hint, clock and scoring authority.
// No audio file, audio API, credential, model tool or SQL execution path exists.
protocol TIAVoiceBackend: AnyObject {
    var canMonitorDuringPlayback: Bool { get }
    func listen(language: String, ready: @escaping () -> Void, activity: @escaping (TimeInterval, Bool) -> Void,
                transcript: @escaping (String, Bool) -> Void, failed: @escaping (String) -> Void)
    func stopListening()
    func speak(_ text: String, language: String, rate: Double,
               range: @escaping (NSRange) -> Void, finished: @escaping () -> Void, failed: @escaping (String) -> Void)
    func stopSpeaking()
}


// A recognizer endpoint is only a text segment boundary. Only acoustic activity
// and a monotonic clock determine when a candidate turn may be sealed.
struct TIAVoiceSilenceGate {
    static let interval: TimeInterval = 5
    private(set) var lastActivity: TimeInterval?
    mutating func observe(_ time: TimeInterval) {
        guard time.isFinite else { return }
        lastActivity = max(lastActivity ?? time, time)
    }
    func remaining(at now: TimeInterval) -> TimeInterval? {
        guard let lastActivity else { return nil }
        return max(0, lastActivity + Self.interval - max(now, lastActivity))
    }
    func maySeal(at now: TimeInterval) -> Bool { remaining(at: now) == 0 }
}

// Runs only on the audio-tap queue, on Apple's echo-cancelled microphone signal.
// A short impulse cannot trigger onset. Low-frequency rumble / high-frequency
// key clicks are rejected; the adaptive noise floor is never learned from speech.
// Acoustic separation is heuristic and must also be checked in hardware UAT.
struct TIACandidateSpeechDetector {
    private var previousInput: Double = 0, highPass: Double = 0, lowPass: Double = 0
    private var noise = 0.001, voicedSeconds: Double = 0
    private(set) var possibleSpeech = false
    mutating func observe(samples: UnsafeBufferPointer<Float>, sampleRate: Double) -> Bool {
        guard sampleRate > 0, !samples.isEmpty else { return false }
        let highCoefficient = exp(-2 * Double.pi * 90 / sampleRate)
        let lowCoefficient = 1 - exp(-2 * Double.pi * 4200 / sampleRate)
        var energy = 0.0, crossings = 0, previous = lowPass
        for sample in samples {
            let value = Double(sample)
            guard value.isFinite else { continue }
            highPass = highCoefficient * (highPass + value - previousInput); previousInput = value
            lowPass += lowCoefficient * (highPass - lowPass)
            energy += lowPass * lowPass
            if (lowPass >= 0) != (previous >= 0) { crossings += 1 }; previous = lowPass
        }
        let rms = sqrt(energy / Double(samples.count))
        let crossingRate = Double(crossings) / Double(samples.count)
        let voiced = rms > max(0.006, noise * 3.5) && crossingRate > 0.003 && crossingRate < 0.32
        possibleSpeech = voiced
        let duration = Double(samples.count) / sampleRate
        if voiced { voicedSeconds += duration }
        else { voicedSeconds = 0; noise = min(0.02, noise * 0.98 + rms * 0.02) }
        return voiced && voicedSeconds >= 0.08
    }
}

// Audio stays in memory. During interviewer playback recognition receives no
// frames until acoustic candidate onset. A bounded 160 ms pre-roll preserves the
// candidate's first syllable while excluding accumulated interviewer narration.
// The lock coordinates the audio tap and main-thread recognizer rotations.
final class TIARecognitionPipe: @unchecked Sendable {
    private let lock = NSLock()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var guardingPlayback = false
    private var preRoll = [AVAudioPCMBuffer]()
    private var preRollSeconds = 0.0
    private let syntheticSink: ((AVAudioPCMBuffer) -> Void)?
    init(syntheticSink: ((AVAudioPCMBuffer) -> Void)? = nil) { self.syntheticSink = syntheticSink }
    func replace(_ value: SFSpeechAudioBufferRecognitionRequest?) {
        lock.lock(); defer { lock.unlock() }
        request = value
        if value == nil { preRoll.removeAll(); preRollSeconds = 0; guardingPlayback = false }
    }
    func guardPlayback(_ value: Bool) {
        lock.lock(); defer { lock.unlock() }
        guardingPlayback = value; preRoll.removeAll(); preRollSeconds = 0
    }
    private func deliver(_ buffer: AVAudioPCMBuffer) {
        if let syntheticSink { syntheticSink(buffer) } else { request?.append(buffer) }
    }
    func append(_ buffer: AVAudioPCMBuffer, candidateOnset: Bool) {
        lock.lock(); defer { lock.unlock() }
        guard buffer.frameLength > 0, buffer.format.sampleRate > 0 else { return }
        if !guardingPlayback { deliver(buffer); return }
        // Audio tap buffers are reused by AVAudioEngine. Retain a bounded copy,
        // never the borrowed pointer, and wipe it on stop/end of playback.
        guard let copy = AVAudioPCMBuffer(pcmFormat: buffer.format, frameCapacity: buffer.frameLength) else { return }
        copy.frameLength = buffer.frameLength
        let source = UnsafeMutableAudioBufferListPointer(UnsafeMutablePointer(mutating: buffer.audioBufferList))
        let destination = UnsafeMutableAudioBufferListPointer(copy.mutableAudioBufferList)
        guard source.count == destination.count else { return }
        for index in source.indices {
            guard let from = source[index].mData, let to = destination[index].mData,
                  destination[index].mDataByteSize >= source[index].mDataByteSize else { return }
            memcpy(to, from, Int(source[index].mDataByteSize))
        }
        preRoll.append(copy); preRollSeconds += Double(copy.frameLength) / copy.format.sampleRate
        while preRollSeconds > 0.16, preRoll.count > 1 {
            let oldest = preRoll.removeFirst()
            preRollSeconds -= Double(oldest.frameLength) / oldest.format.sampleRate
        }
        guard candidateOnset else { return }
        guardingPlayback = false
        for frame in preRoll { deliver(frame) }
        preRoll.removeAll(); preRollSeconds = 0
    }
}

// Permission callbacks can arrive before macOS restores App activation.
// Keep the authorized start pending without capturing in the background.
final class TIAVoiceActivationGate {
    private var pending: (() -> Void)?
    func wait(active: Bool, start: @escaping () -> Void) {
        pending = start
        if active { becameActive() }
    }
    func becameActive() { let start = pending; pending = nil; start?() }
    func cancel() { pending = nil }
}

// AVSpeechSynthesizerDelegate inherits Sendable in recent SDKs. All mutable
// backend state is confined to the main thread; system callbacks re-enter it.
// The audio tap only appends to Apple's thread-safe buffer request.
final class TIALocalVoiceBackend: NSObject, TIAVoiceBackend, AVSpeechSynthesizerDelegate, @unchecked Sendable {
    private let activationGate = TIAVoiceActivationGate()
    private var activationObserver: NSObjectProtocol?
    private let engine = AVAudioEngine()
    private let audioPipe = TIARecognitionPipe()
    private var recognitionSegment = UUID()
    private var completedText = ""
    private let synthesizer = AVSpeechSynthesizer()
    private var task: SFSpeechRecognitionTask?
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var recognizer: SFSpeechRecognizer?
    private var tapInstalled = false
    private var generation = UUID()
    private var utterance: AVSpeechUtterance?
    private var speechRange: ((NSRange) -> Void)?
    private var speechFinished: (() -> Void)?

    override init() {
        super.init(); synthesizer.delegate = self
        activationObserver = NotificationCenter.default.addObserver(
            forName: NSApplication.didBecomeActiveNotification, object: nil, queue: .main
        ) { [weak self] _ in self?.activationGate.becameActive() }
    }
    deinit { if let observer = activationObserver { NotificationCenter.default.removeObserver(observer) } }

    var canMonitorDuringPlayback: Bool {
        AVCaptureDevice.authorizationStatus(for: .audio) == .authorized &&
            SFSpeechRecognizer.authorizationStatus() == .authorized
    }

    func listen(language: String, ready: @escaping () -> Void, activity: @escaping (TimeInterval, Bool) -> Void,
                transcript: @escaping (String, Bool) -> Void, failed: @escaping (String) -> Void) {
        stopListening()
        let token = generation
        // A device/language without the downloaded local recognizer fails closed.
        // We never fall back to Apple's network speech recognition service.
        guard let local = SFSpeechRecognizer(locale: Locale(identifier: language)),
              local.supportsOnDeviceRecognition else { failed("VOICE_ON_DEVICE_UNAVAILABLE"); return }
        func authorized() {
            DispatchQueue.main.async { [weak self] in
                guard let self = self, self.generation == token else { return }
                self.activationGate.wait(active: NSApplication.shared.isActive) { [weak self] in
                    guard let self = self, self.generation == token, NSApplication.shared.isActive else { return }
                    self.start(local, token: token, ready: ready, activity: activity, transcript: transcript, failed: failed)
                }
            }
        }
        func microphonePermission() {
            guard self.generation == token else { return }
            switch AVCaptureDevice.authorizationStatus(for: .audio) {
            case .authorized: authorized()
            case .notDetermined:
                AVCaptureDevice.requestAccess(for: .audio) { granted in
                    DispatchQueue.main.async { [weak self] in
                        guard let self = self, self.generation == token else { return }
                        if granted { authorized() } else { failed("VOICE_MIC_PERMISSION_DENIED") }
                    }
                }
            default: failed("VOICE_MIC_PERMISSION_DENIED")
            }
        }
        switch SFSpeechRecognizer.authorizationStatus() {
        case .authorized: microphonePermission()
        case .notDetermined:
            SFSpeechRecognizer.requestAuthorization { status in
                DispatchQueue.main.async { [weak self] in
                    guard let self = self, self.generation == token else { return }
                    if status == .authorized { microphonePermission() }
                    else { failed("VOICE_SPEECH_PERMISSION_DENIED") }
                }
            }
        default: failed("VOICE_SPEECH_PERMISSION_DENIED")
        }
    }

    private func start(_ local: SFSpeechRecognizer, token: UUID, ready: @escaping () -> Void,
                       activity: @escaping (TimeInterval, Bool) -> Void,
                       transcript: @escaping (String, Bool) -> Void, failed: @escaping (String) -> Void) {
        guard generation == token, local.supportsOnDeviceRecognition, local.isAvailable else {
            failed("VOICE_ON_DEVICE_UNAVAILABLE"); return
        }
        let input = engine.inputNode
        // Apple's Voice Processing I/O removes device playback from the input.
        // Never silently fall back to a raw microphone during interviewer audio.
        do { try input.setVoiceProcessingEnabled(true) }
        catch { failed("VOICE_ECHO_CANCELLATION_UNAVAILABLE"); return }
        guard input.isVoiceProcessingEnabled else { failed("VOICE_ECHO_CANCELLATION_UNAVAILABLE"); return }
        input.isVoiceProcessingBypassed = false
        let format = input.outputFormat(forBus: 0)
        guard format.channelCount > 0, format.sampleRate > 0 else { failed("VOICE_MIC_UNAVAILABLE"); return }
        completedText = ""; recognizer = local
        beginSegment(local, token: token, transcript: transcript, failed: failed)
        audioPipe.guardPlayback(utterance != nil)
        let pipe = audioPipe
        var detector = TIACandidateSpeechDetector()
        input.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
            guard let samples = buffer.floatChannelData?[0], buffer.frameLength > 0 else { return }
            let spoken = detector.observe(samples: UnsafeBufferPointer(start: samples, count: Int(buffer.frameLength)),
                                          sampleRate: buffer.format.sampleRate)
            // Even the first plausible frame holds off a pending seal. The
            // sustained onset threshold gates barge-in, not silence continuity.
            if detector.possibleSpeech {
                let time = ProcessInfo.processInfo.systemUptime
                DispatchQueue.main.async {
                    guard let self, self.generation == token else { return }
                    activity(time, spoken)
                }
            }
            pipe.append(buffer, candidateOnset: spoken)
        }
        tapInstalled = true
        do { engine.prepare(); try engine.start(); ready() }
        catch { stopListening(); failed("VOICE_MIC_UNAVAILABLE") }
    }

    private func beginSegment(_ local: SFSpeechRecognizer, token: UUID,
                              transcript: @escaping (String, Bool) -> Void, failed: @escaping (String) -> Void) {
        recognitionSegment = UUID(); let segment = recognitionSegment
        let previousTask = task, previousRequest = request
        let bufferRequest = SFSpeechAudioBufferRecognitionRequest()
        bufferRequest.requiresOnDeviceRecognition = true
        bufferRequest.shouldReportPartialResults = true
        bufferRequest.taskHint = .dictation
        request = bufferRequest; audioPipe.replace(bufferRequest)
        previousRequest?.endAudio(); previousTask?.cancel()
        task = local.recognitionTask(with: bufferRequest) { [weak self] result, error in
            DispatchQueue.main.async {
                guard let self, self.generation == token, self.recognitionSegment == segment else { return }
                if let result {
                    let segmentText = result.bestTranscription.formattedString.trimmingCharacters(in: .whitespacesAndNewlines)
                    let wholeText = [self.completedText, segmentText].filter { !$0.isEmpty }.joined(separator: " ")
                    transcript(wholeText, result.isFinal)
                    guard self.generation == token else { return }
                    if result.isFinal {
                        self.completedText = wholeText
                        // Keep the mic, acoustic clock and accumulated text alive.
                        // Finalization never seals a turn or causes a paid request.
                        self.beginSegment(local, token: token, transcript: transcript, failed: failed)
                        return
                    }
                }
                // A backend failure preserves the draft; it never sends or skips.
                if error != nil { failed("VOICE_RECOGNITION_FAILED") }
            }
        }
    }

    func stopListening() {
        activationGate.cancel()
        generation = UUID()
        engine.stop()
        if tapInstalled { engine.inputNode.removeTap(onBus: 0); tapInstalled = false }
        recognitionSegment = UUID(); audioPipe.replace(nil)
        request?.endAudio(); task?.cancel(); completedText = ""
        task = nil; request = nil; recognizer = nil
    }

    func speak(_ text: String, language: String, rate: Double,
               range: @escaping (NSRange) -> Void, finished: @escaping () -> Void, failed: @escaping (String) -> Void) {
        stopSpeaking()
        // Select only an installed system voice. No asset download is initiated.
        guard let voice = AVSpeechSynthesisVoice.speechVoices().first(where: { $0.language == language }) else {
            failed("VOICE_SPEAKER_UNAVAILABLE"); return
        }
        let speech = AVSpeechUtterance(string: text)
        speech.voice = voice
        speech.rate = min(AVSpeechUtteranceMaximumSpeechRate,
                          max(AVSpeechUtteranceMinimumSpeechRate, AVSpeechUtteranceDefaultSpeechRate * Float(rate)))
        utterance = speech; speechRange = range; speechFinished = finished
        audioPipe.guardPlayback(true)
        synthesizer.speak(speech)
    }
    func stopSpeaking() {
        audioPipe.guardPlayback(false)
        utterance = nil; speechRange = nil; speechFinished = nil
        synthesizer.stopSpeaking(at: .immediate)
    }
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, willSpeakRangeOfSpeechString range: NSRange,
                           utterance: AVSpeechUtterance) {
        DispatchQueue.main.async { [weak self] in
            guard let self = self, self.utterance === utterance else { return }; self.speechRange?(range)
        }
    }
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        DispatchQueue.main.async { [weak self] in self?.finish(utterance) }
    }
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        DispatchQueue.main.async { [weak self] in self?.finish(utterance) }
    }
    private func finish(_ utterance: AVSpeechUtterance) {
        guard self.utterance === utterance else { return }
        let callback = speechFinished
        audioPipe.guardPlayback(false)
        self.utterance = nil; speechRange = nil; speechFinished = nil
        callback?()
    }
}

// Used only by the existing --ui-*-test builds. No microphone, speech engine,
// permission request or network transport is constructed in this backend.
private final class TIASilentVoiceBackend: TIAVoiceBackend {
    var canMonitorDuringPlayback: Bool { true }
    func listen(language: String, ready: @escaping () -> Void, activity: @escaping (TimeInterval, Bool) -> Void,
                transcript: @escaping (String, Bool) -> Void, failed: @escaping (String) -> Void) { ready() }
    func stopListening() {}
    func speak(_ text: String, language: String, rate: Double,
               range: @escaping (NSRange) -> Void, finished: @escaping () -> Void, failed: @escaping (String) -> Void) {
        DispatchQueue.main.async { range(NSRange(location: 0, length: (text as NSString).length)); finished() }
    }
    func stopSpeaking() {}
}

final class TIAVoiceCompanion {
    static let maxTranscriptBytes = 4096
    static let silenceSeconds = TIAVoiceSilenceGate.interval
    var onChange: (([String: Any]) -> Void)?
    var onSubmit: ((String, String) -> Void)?
    private let backend: TIAVoiceBackend
    private let testing: Bool
    private var generation = UUID()
    private var speechGeneration = UUID()
    private var silenceTimer: Timer?
    private var silenceGate = TIAVoiceSilenceGate()
    private var syntheticTimeOffset: TimeInterval = 0
    private var now: TimeInterval { ProcessInfo.processInfo.systemUptime + syntheticTimeOffset }
    private var sessionKey: String?
    private var enteredRooms = Set<String>()
    private var latestReplyID: String?
    private var latestReplyText = ""
    private var eligible = false
    private var canSend = false
    private var busy = false
    private var enabled = false
    private var requested = false
    private var listening = false
    private var candidateDetected = false
    private var permissionPending = false
    private var speaking = false
    private var muted = false
    private var handsfree = false
    private var submitting = false
    private var language = "en-US"
    private var rate = 1.2
    private var kind = "clarify"
    private var draft = ""
    private var partial = ""
    private var caption = ""
    private var wordRange = NSRange(location: 0, length: 0)
    private var error: String?
    private var paused = false

    convenience init(testing: Bool) {
        self.init(backend: testing ? TIASilentVoiceBackend() : TIALocalVoiceBackend(), testing: testing)
    }
    init(backend: TIAVoiceBackend, testing: Bool = true) { self.backend = backend; self.testing = testing }

    static func validate(action: String, params: [String: Any]) -> Bool {
        switch action {
        case "voice_listen", "voice_pause", "voice_replay", "voice_clear", "voice_send": return params.isEmpty
        case "voice_mute", "voice_handsfree":
            let key = action == "voice_mute" ? "muted" : "enabled"
            guard Set(params.keys) == [key], let value = params[key] as? NSNumber else { return false }
            return CFGetTypeID(value) == CFBooleanGetTypeID()
        case "voice_kind":
            return Set(params.keys) == ["kind"] && ["clarify", "plan", "test", "help"].contains(params["kind"] as? String ?? "")
        case "voice_settings":
            guard Set(params.keys) == ["language", "rate"], ["en-US", "zh-CN"].contains(params["language"] as? String ?? ""),
                  let number = params["rate"] as? NSNumber, CFGetTypeID(number) != CFBooleanGetTypeID() else { return false }
            return [0.8, 1.0, 1.2].contains(number.doubleValue)
        case "voice_draft":
            guard Set(params.keys) == ["text"], let text = params["text"] as? String else { return false }
            return text.utf8.count <= maxTranscriptBytes
        default: return false
        }
    }

    var isAwaitingPermission: Bool { permissionPending }

    var publicState: [String: Any] {
        let status: String
        if !eligible { status = "OFF" }
        else if submitting || busy { status = "WAITING" }
        else if speaking { status = "SPEAKING" }
        else if permissionPending { status = "PERMISSION" }
        else if listening { status = "LISTENING" }
        else if error != nil { status = "UNAVAILABLE" }
        else if !draft.isEmpty { status = "DRAFT" }
        else if paused { status = "PAUSED" }
        else { status = "READY" }
        return ["schema": "tia-local-voice/v1", "available": eligible, "eligible": eligible,
                "can_listen": eligible && canSend && !busy && !submitting,
                "status": status, "listening_requested": requested, "listening": listening,
                "speaking": speaking, "muted": muted, "handsfree": handsfree,
                "silence_seconds": Self.silenceSeconds, "barge_in_monitoring": speaking && listening,
                "language": language, "rate": rate, "kind": kind, "draft": draft, "partial": partial,
                "caption": caption, "word_start": wordRange.location, "word_length": wordRange.length,
                "caption_range": ["location": wordRange.location, "length": wordRange.length],
                "error": error as Any? ?? NSNull()]
    }

    func update(host: [String: Any], provider: [String: Any], busy: Bool) {
        let preview = host["live_preview"] as? [String: Any] ?? [:]
        let session = preview["session"] as? [String: Any] ?? [:]
        let question = preview["question"] as? [String: Any] ?? [:]
        let questionData = (try? JSONSerialization.data(withJSONObject: question, options: [.sortedKeys])) ?? Data()
        let questionHash = SHA256.hash(data: questionData).map { String(format: "%02x", $0) }.joined()
        let identity = (session["session_id"] as? String ?? "") + ":" + questionHash
        let providerState = provider["state"] as? String ?? "offline"
        // An already verified credential remains authenticated while its next
        // request is connecting or has a recoverable failure. Preserve the
        // draft/consent through that request; only live-verified may start input.
        let verifiedCredential = provider["authenticated"] as? Bool == true &&
            provider["live_enabled"] as? Bool == true &&
            ["live-verified", "connecting", "unavailable"].contains(providerState)
        let active = host["screen"] as? String == "LIVE_PREVIEW" && verifiedCredential &&
            preview["closed"] as? Bool == false && session["phase"] as? String == "INTERVIEWING"
        let events = session["events"] as? [[String: Any]] ?? []
        let last = events.last { $0["actor"] as? String == "interviewer" && $0["provenance"] as? String == "LIVE_MODEL" }
        let replyID = last?["id"] as? String
        let replyText = (last?["payload"] as? [String: Any])?["text"] as? String ?? ""
        let newRoom = sessionKey != identity || !eligible
        let freshEntry = newRoom && !enteredRooms.contains(identity) &&
            !events.contains { $0["actor"] as? String == "candidate" }
        if !active {
            if eligible || requested || speaking || submitting { clearRoom() }
            eligible = false; canSend = false; self.busy = false; sessionKey = nil
            emit(); return
        }
        if newRoom {
            clearRoom(); paused = false; sessionKey = identity; latestReplyID = replyID
            enteredRooms.insert(identity)
            latestReplyText = boundedReply(replyText); caption = latestReplyText
        }
        eligible = true; canSend = providerState == "live-verified" && preview["can_send"] as? Bool == true
        self.busy = busy || preview["pending"] as? Bool == true
        // Owner-approved room default. Snapshots, reconnects and recovered
        // conversations must not undo a pause or start capture again.
        if freshEntry {
            enabled = true; requested = true; handsfree = true; muted = false; kind = "clarify"
            if !self.busy { speakLatest() }
        }
        if self.busy || !canSend {
            if !partial.isEmpty && draft.isEmpty {
                draft = partial; partial = ""; requested = false
            }
            suspendListening()
        }
        if !newRoom, replyID != nil, replyID != latestReplyID {
            latestReplyID = replyID; latestReplyText = boundedReply(replyText)
            caption = latestReplyText; wordRange = NSRange(location: 0, length: 0)
            if enabled && !muted && !self.busy { speakLatest() }
        }
        resumeIfAllowed(); emit()
    }

    @discardableResult func perform(action: String, params: [String: Any]) -> String? {
        guard Self.validate(action: action, params: params) else { return "VOICE_INVALID_ACTION" }
        if action == "voice_pause" { pause(stopSpeech: false); emit(); return nil }
        if action == "voice_mute" {
            muted = params["muted"] as! Bool
            if muted { cancelSpeech(); resumeIfAllowed() }
            else if eligible { enabled = true }
            emit(); return nil
        }
        guard eligible else { return "VOICE_VERIFIED_ROOM_REQUIRED" }
        error = nil
        switch action {
        case "voice_listen":
            guard !busy && !submitting && canSend else { return "VOICE_TURN_UNAVAILABLE" }
            guard draft.isEmpty else { return "VOICE_DRAFT_PENDING" }
            enabled = true; requested = true; paused = false
            cancelSpeech(); resumeIfAllowed()
        case "voice_replay":
            guard !busy && !submitting else { return "VOICE_TURN_UNAVAILABLE" }
            guard !muted else { return "VOICE_SPEAKER_MUTED" }
            guard !latestReplyText.isEmpty else { return "VOICE_NO_COMMITTED_REPLY" }
            enabled = true; paused = false; speakLatest()
        case "voice_handsfree":
            guard !submitting else { return "VOICE_TURN_UNAVAILABLE" }
            handsfree = params["enabled"] as! Bool
            // Uses the already authorized native model request budget.
            // It never starts recording or sends an existing draft by itself.
        case "voice_kind":
            guard !submitting else { return "VOICE_TURN_UNAVAILABLE" }
            kind = params["kind"] as! String
        case "voice_settings":
            guard !submitting else { return "VOICE_TURN_UNAVAILABLE" }
            pause(); language = params["language"] as! String; rate = (params["rate"] as! NSNumber).doubleValue
        case "voice_draft":
            guard !submitting else { return "VOICE_TURN_UNAVAILABLE" }
            suspendListening(); requested = false; draft = params["text"] as! String; partial = ""
        case "voice_clear":
            guard !submitting else { return "VOICE_TURN_UNAVAILABLE" }
            suspendListening(); requested = false; draft = ""; partial = ""
        case "voice_send":
            guard !busy && !submitting && canSend else { return "VOICE_TURN_UNAVAILABLE" }
            if listening || permissionPending {
                if draft.isEmpty { draft = partial }; suspendListening(); partial = ""
            }
            guard !draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return "VOICE_DRAFT_EMPTY" }
            submit()
            if let failure = error { emit(); return failure }
        default: return "VOICE_INVALID_ACTION"
        }
        emit(); return nil
    }

    // App resign-active/disconnect/close: real capture and synthesis stop and
    // every pending callback is invalidated. Explicit Listen is needed again.
    func stop() { clearRoom(); emit() }
    func submissionFinished(ok: Bool) {
        guard submitting else { return }
        submitting = false
        if ok { draft = ""; partial = ""; error = nil; resumeIfAllowed() }
        else { pause(); error = "VOICE_SUBMISSION_FAILED" }
        emit()
    }

    // Native-only fixture entrypoint. Not present in BridgePolicy's allowlist.
    func injectSyntheticTranscript(_ text: String, final: Bool) {
        guard testing, listening, eligible, !busy else { return }
        candidateActivity(at: now, token: generation)
        received(text, final: final, token: generation)
    }
    func finishSyntheticUtterance() {
        guard testing, listening else { return }
        // Native test fixture clock only; never reachable from the WebKit bridge.
        syntheticTimeOffset += silenceGate.remaining(at: now) ?? Self.silenceSeconds
        finishUtterance(token: generation)
    }

    func injectSyntheticActivity() {
        guard testing else { return }; candidateActivity(at: now, token: generation)
    }
    func advanceSyntheticTime(by seconds: TimeInterval) {
        guard testing, seconds.isFinite, seconds >= 0, seconds <= 60 else { return }
        syntheticTimeOffset += seconds
        finishUtterance(token: generation)
    }

    private func boundedReply(_ text: String) -> String { text.utf8.count <= 16384 ? text : "" }
    private func timer(after seconds: TimeInterval, fire: @escaping () -> Void) -> Timer {
        let timer = Timer(timeInterval: seconds, repeats: false) { _ in fire() }
        // Endpoints continue during native controls/menu tracking, not just the
        // default run-loop mode; moving the companion never extends recording.
        RunLoop.main.add(timer, forMode: .common)
        return timer
    }
    private func emit() { onChange?(publicState) }
    private func clearRoom() {
        pause(); submitting = false; enabled = false; draft = ""; partial = ""; caption = ""
        wordRange = NSRange(location: 0, length: 0); latestReplyID = nil; latestReplyText = ""; error = nil
    }
    private func pause(stopSpeech: Bool = true) {
        if !partial.isEmpty && draft.isEmpty { draft = partial }
        requested = false; paused = true
        suspendListening(); if stopSpeech { cancelSpeech() }; partial = ""
    }
    private func suspendListening() {
        generation = UUID(); silenceTimer?.invalidate(); silenceTimer = nil
        silenceGate = TIAVoiceSilenceGate(); candidateDetected = false
        if listening || permissionPending { backend.stopListening() }
        listening = false; permissionPending = false
    }
    private func cancelSpeech() {
        speechGeneration = UUID(); backend.stopSpeaking(); speaking = false
        wordRange = NSRange(location: 0, length: 0)
    }
    private func resumeIfAllowed() {
        guard eligible && canSend && requested && !busy && !submitting &&
              (!speaking || backend.canMonitorDuringPlayback) &&
              !listening && !permissionPending && draft.isEmpty else { return }
        generation = UUID(); let token = generation
        partial = ""; syntheticTimeOffset = 0; permissionPending = true
        backend.listen(language: language, ready: { [weak self] in
            guard let self = self, self.generation == token, self.eligible, self.requested else { return }
            self.permissionPending = false; self.listening = true
            self.emit()
        }, activity: { [weak self] time, confirmed in
            self?.candidateActivity(at: time, confirmed: confirmed, token: token)
        }, transcript: { [weak self] text, final in
            self?.received(text, final: final, token: token)
        }, failed: { [weak self] code in
            guard let self = self, self.generation == token else { return }
            self.pause(); self.error = code; self.emit()
        })
    }
    private func candidateActivity(at time: TimeInterval, confirmed: Bool = true, token: UUID) {
        guard generation == token, listening, eligible, requested, !busy, !submitting else { return }
        silenceGate.observe(time)
        if confirmed { candidateDetected = true }
        if speaking && confirmed { cancelSpeech() }
        armSilenceCheck(token: token)
        emit()
    }
    private func armSilenceCheck(token: UUID) {
        guard let remaining = silenceGate.remaining(at: now) else { return }
        silenceTimer?.invalidate()
        silenceTimer = timer(after: max(0.01, remaining)) { [weak self] in self?.finishUtterance(token: token) }
    }
    private func received(_ text: String, final: Bool, token: UUID) {
        guard generation == token, listening, eligible, !busy, !submitting else { return }
        guard text.utf8.count <= Self.maxTranscriptBytes else {
            pause(); error = "VOICE_TRANSCRIPT_TOO_LONG"; emit(); return
        }
        // Text and isFinal do not prove acoustic silence. A recognizer may emit
        // final while the candidate is still speaking, or repeat unchanged text.
        // Never promote playback-only recognition to a candidate turn.
        guard !speaking || candidateDetected else { return }
        partial = text
        if !speaking, silenceGate.maySeal(at: now) { finishUtterance(token: token) }
        emit()
    }
    private func finishUtterance(token: UUID) {
        guard generation == token, listening, eligible, !busy, !submitting else { return }
        guard silenceGate.maySeal(at: now) else { armSilenceCheck(token: token); return }
        guard candidateDetected else { return }
        let value = partial.trimmingCharacters(in: .whitespacesAndNewlines)
        // Empty recognition cannot spend a request. Continue listening for a
        // usable transcript rather than treating an empty endpoint as a turn.
        guard !value.isEmpty else { return }
        suspendListening(); partial = ""
        draft = value
        if handsfree && canSend { submit() }
        else { requested = false }
        emit()
    }
    private func submit() {
        guard let send = onSubmit else { requested = false; error = "VOICE_SUBMISSION_UNAVAILABLE"; return }
        cancelSpeech(); suspendListening(); submitting = true
        if !handsfree { requested = false }
        let text = draft; let candidateKind = kind
        emit(); send(candidateKind, text)
    }
    private func speakLatest() {
        guard eligible, !muted, !latestReplyText.isEmpty else { return }
        if !partial.isEmpty && draft.isEmpty {
            draft = partial; partial = ""; requested = false
        }
        suspendListening(); cancelSpeech(); speaking = true; caption = latestReplyText
        let token = speechGeneration
        backend.speak(latestReplyText, language: language, rate: rate, range: { [weak self] range in
            guard let self = self, self.speechGeneration == token, self.speaking,
                  range.location >= 0, range.length >= 0,
                  range.location <= (self.caption as NSString).length,
                  range.length <= (self.caption as NSString).length - range.location else { return }
            self.wordRange = range; self.emit()
        }, finished: { [weak self] in
            guard let self = self, self.speechGeneration == token else { return }
            self.speaking = false; self.wordRange = NSRange(location: 0, length: 0)
            self.resumeIfAllowed(); self.emit()
        }, failed: { [weak self] code in
            guard let self = self, self.speechGeneration == token else { return }
            self.pause(); self.error = code; self.emit()
        })
        // Capture may run alongside speech only with permissions already granted
        // and the echo-cancelled native backend. Permission sheets wait until the
        // introduction ends; denying permission cannot trigger a request.
        resumeIfAllowed()
    }
}
