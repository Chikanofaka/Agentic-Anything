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
    func listen(language: String, ready: @escaping () -> Void,
                transcript: @escaping (String, Bool) -> Void, failed: @escaping (String) -> Void)
    func stopListening()
    func speak(_ text: String, language: String, rate: Double,
               range: @escaping (NSRange) -> Void, finished: @escaping () -> Void, failed: @escaping (String) -> Void)
    func stopSpeaking()
}

// AVSpeechSynthesizerDelegate inherits Sendable in recent SDKs. All mutable
// backend state is confined to the main thread; system callbacks re-enter it.
// The audio tap only appends to Apple's thread-safe buffer request.
final class TIALocalVoiceBackend: NSObject, TIAVoiceBackend, AVSpeechSynthesizerDelegate, @unchecked Sendable {
    private let engine = AVAudioEngine()
    private let synthesizer = AVSpeechSynthesizer()
    private var task: SFSpeechRecognitionTask?
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var recognizer: SFSpeechRecognizer?
    private var tapInstalled = false
    private var generation = UUID()
    private var utterance: AVSpeechUtterance?
    private var speechRange: ((NSRange) -> Void)?
    private var speechFinished: (() -> Void)?

    override init() { super.init(); synthesizer.delegate = self }

    func listen(language: String, ready: @escaping () -> Void,
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
                guard NSApplication.shared.isActive else { failed("VOICE_APP_INACTIVE"); return }
                self.start(local, token: token, ready: ready, transcript: transcript, failed: failed)
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
                       transcript: @escaping (String, Bool) -> Void, failed: @escaping (String) -> Void) {
        guard generation == token, local.supportsOnDeviceRecognition, local.isAvailable else {
            failed("VOICE_ON_DEVICE_UNAVAILABLE"); return
        }
        let input = engine.inputNode
        let format = input.outputFormat(forBus: 0)
        guard format.channelCount > 0, format.sampleRate > 0 else { failed("VOICE_MIC_UNAVAILABLE"); return }
        let bufferRequest = SFSpeechAudioBufferRecognitionRequest()
        bufferRequest.requiresOnDeviceRecognition = true
        bufferRequest.shouldReportPartialResults = true
        bufferRequest.taskHint = .dictation
        request = bufferRequest; recognizer = local
        input.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            bufferRequest.append(buffer)
        }
        tapInstalled = true
        task = local.recognitionTask(with: bufferRequest) { [weak self] result, error in
            DispatchQueue.main.async {
                guard let self = self, self.generation == token else { return }
                if let result = result { transcript(result.bestTranscription.formattedString, result.isFinal) }
                // Do not forward localized OS error descriptions or underlying data.
                if error != nil, self.generation == token { failed("VOICE_RECOGNITION_FAILED") }
            }
        }
        do { engine.prepare(); try engine.start(); ready() }
        catch { stopListening(); failed("VOICE_MIC_UNAVAILABLE") }
    }

    func stopListening() {
        generation = UUID()
        engine.stop()
        if tapInstalled { engine.inputNode.removeTap(onBus: 0); tapInstalled = false }
        request?.endAudio(); task?.cancel()
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
        synthesizer.speak(speech)
    }
    func stopSpeaking() {
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
        self.utterance = nil; speechRange = nil; speechFinished = nil
        callback?()
    }
}

// Used only by the existing --ui-*-test builds. No microphone, speech engine,
// permission request or network transport is constructed in this backend.
private final class TIASilentVoiceBackend: TIAVoiceBackend {
    func listen(language: String, ready: @escaping () -> Void,
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
    static let silenceSeconds = 1.5
    static let utteranceSeconds = 45.0
    var onChange: (([String: Any]) -> Void)?
    var onSubmit: ((String, String) -> Void)?
    private let backend: TIAVoiceBackend
    private let testing: Bool
    private var generation = UUID()
    private var speechGeneration = UUID()
    private var silenceTimer: Timer?
    private var durationTimer: Timer?
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
    private var permissionPending = false
    private var speaking = false
    private var muted = false
    private var handsfree = false
    private var submitting = false
    private var language = "en-US"
    private var rate = 1.0
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
                draft = partial; partial = ""; requested = false; handsfree = false
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
        received(text, final: final, token: generation)
    }
    func finishSyntheticUtterance() {
        guard testing, listening else { return }; finishUtterance(token: generation)
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
        requested = false; handsfree = false; paused = true
        suspendListening(); if stopSpeech { cancelSpeech() }; partial = ""
    }
    private func suspendListening() {
        generation = UUID(); silenceTimer?.invalidate(); silenceTimer = nil
        durationTimer?.invalidate(); durationTimer = nil
        if listening || permissionPending { backend.stopListening() }
        listening = false; permissionPending = false
    }
    private func cancelSpeech() {
        speechGeneration = UUID(); backend.stopSpeaking(); speaking = false
        wordRange = NSRange(location: 0, length: 0)
    }
    private func resumeIfAllowed() {
        guard eligible && canSend && requested && !busy && !submitting && !speaking &&
              !listening && !permissionPending && draft.isEmpty else { return }
        generation = UUID(); let token = generation
        partial = ""; permissionPending = true
        backend.listen(language: language, ready: { [weak self] in
            guard let self = self, self.generation == token, self.eligible, self.requested else { return }
            self.permissionPending = false; self.listening = true
            self.durationTimer = self.timer(after: Self.utteranceSeconds) { [weak self] in
                self?.finishUtterance(token: token)
            }
            self.emit()
        }, transcript: { [weak self] text, final in
            self?.received(text, final: final, token: token)
        }, failed: { [weak self] code in
            guard let self = self, self.generation == token else { return }
            self.pause(); self.error = code; self.emit()
        })
    }
    private func received(_ text: String, final: Bool, token: UUID) {
        guard generation == token, listening, eligible, !busy, !submitting else { return }
        guard text.utf8.count <= Self.maxTranscriptBytes else {
            pause(); error = "VOICE_TRANSCRIPT_TOO_LONG"; emit(); return
        }
        let changed = text != partial; partial = text
        if final { finishUtterance(token: token); return }
        if changed {
            silenceTimer?.invalidate()
            silenceTimer = timer(after: Self.silenceSeconds) { [weak self] in
                self?.finishUtterance(token: token)
            }
        }
        emit()
    }
    private func finishUtterance(token: UUID) {
        guard generation == token, listening, eligible, !busy, !submitting else { return }
        let value = partial.trimmingCharacters(in: .whitespacesAndNewlines)
        suspendListening(); partial = ""
        guard !value.isEmpty else { requested = false; handsfree = false; error = "VOICE_NO_SPEECH"; emit(); return }
        draft = value
        if handsfree && canSend { submit() }
        else { requested = false }
        emit()
    }
    private func submit() {
        guard let send = onSubmit else { requested = false; handsfree = false; error = "VOICE_SUBMISSION_UNAVAILABLE"; return }
        cancelSpeech(); suspendListening(); submitting = true
        if !handsfree { requested = false }
        let text = draft; let candidateKind = kind
        emit(); send(candidateKind, text)
    }
    private func speakLatest() {
        guard eligible, !muted, !latestReplyText.isEmpty else { return }
        if !partial.isEmpty && draft.isEmpty {
            draft = partial; partial = ""; requested = false; handsfree = false
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
    }
}
