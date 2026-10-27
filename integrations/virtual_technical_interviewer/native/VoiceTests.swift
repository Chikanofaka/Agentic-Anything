import Foundation
import AVFoundation

private final class TIAVoiceMock: TIAVoiceBackend {
    var canMonitorDuringPlayback = false
    var autoReady = true
    var listenCount = 0
    var stopCount = 0
    var speechStopCount = 0
    var said: [String] = []
    var languages: [String] = []
    var rates: [Double] = []
    var ready: (() -> Void)?
    var transcript: ((String, Bool) -> Void)?
    var rawTranscript: ((String, Bool) -> Void)?
    var activity: ((TimeInterval, Bool) -> Void)?
    var failed: ((String) -> Void)?
    var range: ((NSRange) -> Void)?
    var finished: (() -> Void)?
    var speechFailed: ((String) -> Void)?
    func listen(language: String, ready: @escaping () -> Void, activity: @escaping (TimeInterval, Bool) -> Void,
                transcript: @escaping (String, Bool) -> Void, failed: @escaping (String) -> Void) {
        listenCount += 1; languages.append(language)
        self.ready = ready; self.activity = activity; self.rawTranscript = transcript
        self.transcript = { text, final in
            activity(ProcessInfo.processInfo.systemUptime, true)
            transcript(text, final)
        }
        self.failed = failed
        if autoReady { ready() }
    }
    func stopListening() { stopCount += 1 }
    func speak(_ text: String, language: String, rate: Double,
               range: @escaping (NSRange) -> Void, finished: @escaping () -> Void, failed: @escaping (String) -> Void) {
        said.append(text); languages.append(language); rates.append(rate)
        self.range = range; self.finished = finished; self.speechFailed = failed
    }
    func stopSpeaking() { speechStopCount += 1 }
}

func runVoiceTests() -> Int32 {
    var checks = 0, failures = 0
    func check(_ label: String, _ condition: @autoclosure () -> Bool) {
        checks += 1
        if condition() { print("PASS voice " + label) }
        else { failures += 1; print("FAIL voice " + label) }
    }
    func provider(_ state: String = "live-verified", authenticated: Bool? = nil) -> [String: Any] {
        ["state": state, "authenticated": authenticated ?? (state == "live-verified"), "live_enabled": state != "offline"]
    }
    func host(_ id: String = "question-1", reply: Int = 1, text: String = "Explain your plan.",
              provenance: String = "LIVE_MODEL", pending: Bool = false, closed: Bool = false,
              canSend: Bool = true, screen: String = "LIVE_PREVIEW") -> [String: Any] {
        ["screen": screen, "live_preview": [
            "question": ["id": id, "task": "Return customer identifiers."],
            "session": ["session_id": id, "phase": closed ? "CLOSED" : "INTERVIEWING", "events": [
                ["id": "\(id):\(reply)", "actor": "interviewer", "provenance": provenance,
                 "payload": ["text": text]]]],
            "pending": pending, "closed": closed, "can_send": canSend]]
    }
    func fixture() -> (TIAVoiceCompanion, TIAVoiceMock) {
        let backend = TIAVoiceMock()
        let companion = TIAVoiceCompanion(backend: backend)
        companion.update(host: host(), provider: provider(), busy: false)
        // Existing manual-mode regressions explicitly select paused/manual mode.
        companion.stop()
        companion.perform(action: "voice_handsfree", params: ["enabled": false])
        companion.update(host: host(), provider: provider(), busy: false)
        backend.listenCount = 0; backend.stopCount = 0; backend.said = []
        return (companion, backend)
    }
    func bool(_ voice: TIAVoiceCompanion, _ key: String) -> Bool { voice.publicState[key] as? Bool == true }
    func string(_ voice: TIAVoiceCompanion, _ key: String) -> String { voice.publicState[key] as? String ?? "" }

    for action in ["voice_listen", "voice_pause", "voice_replay", "voice_clear", "voice_send"] {
        check("exact empty command \(action)", TIAVoiceCompanion.validate(action: action, params: [:]))
        check("no command extras \(action)", !TIAVoiceCompanion.validate(action: action, params: ["text": "injected"]))
    }
    for kind in ["clarify", "plan", "test", "help"] {
        check("allowed candidate kind \(kind)", TIAVoiceCompanion.validate(action: "voice_kind", params: ["kind": kind]))
    }
    for kind in ["implement", "SQL", "score", "run", "admin"] {
        check("no authority-bearing kind \(kind)", !TIAVoiceCompanion.validate(action: "voice_kind", params: ["kind": kind]))
    }
    check("no arbitrary speech command", !TIAVoiceCompanion.validate(action: "voice_speak", params: ["text": "untrusted"]))
    check("no renderer synthetic transcript", !TIAVoiceCompanion.validate(action: "voice_inject", params: ["text": "untrusted"]))
    check("exact boolean mute", TIAVoiceCompanion.validate(action: "voice_mute", params: ["muted": true]))
    check("numeric boolean rejected", !TIAVoiceCompanion.validate(action: "voice_mute", params: ["muted": 1]))
    check("handsfree consent parameter exact", !TIAVoiceCompanion.validate(action: "voice_handsfree", params: ["enabled": true, "paidConsent": true]))
    check("UTF8 draft bound", !TIAVoiceCompanion.validate(action: "voice_draft", params: ["text": String(repeating: "中", count: 1366)]))
    check("exact 4096-byte draft", TIAVoiceCompanion.validate(action: "voice_draft", params: ["text": String(repeating: "x", count: 4096)]))
    check("rate cannot be boolean", !TIAVoiceCompanion.validate(action: "voice_settings", params: ["language": "en-US", "rate": true]))
    check("rate bounded", !TIAVoiceCompanion.validate(action: "voice_settings", params: ["language": "en-US", "rate": 2.0]))
    check("language allowlist", !TIAVoiceCompanion.validate(action: "voice_settings", params: ["language": "zz-ZZ", "rate": 1.0]))

    do {
        let voice = TIAVoiceCompanion(backend: TIAVoiceMock())
        check("unverified room rejects recording", voice.perform(action: "voice_listen", params: [:]) == "VOICE_VERIFIED_ROOM_REQUIRED")
        voice.update(host: host(), provider: provider("activated-unverified"), busy: false)
        check("stored credential is not verification", !bool(voice, "eligible"))
        voice.update(host: host(screen: "ROOM"), provider: provider(), busy: false)
        check("tutorial cannot use live voice submit", !bool(voice, "eligible"))
        voice.update(host: host(), provider: provider(), busy: false)
        check("verified room becomes ready", bool(voice, "eligible") && bool(voice, "handsfree") && bool(voice, "speaking"))
        voice.stop()
    }
    do {
        let (voice, backend) = fixture()
        var sends: [(String, String)] = []
        voice.onSubmit = { sends.append(($0, $1)) }
        check("no restored autoplay or microphone", backend.listenCount == 0 && backend.said.isEmpty)
        check("initial committed caption visible without playback", string(voice, "caption") == "Explain your plan.")
        voice.update(host: host(reply: 2, text: "Another verified reply."), provider: provider(), busy: false)
        check("voice needs explicit opt-in", backend.said.isEmpty)
        check("explicit listen accepted", voice.perform(action: "voice_listen", params: [:]) == nil && bool(voice, "listening"))
        backend.transcript?("Clarify the tie rule", false)
        check("partial caption never submits", string(voice, "partial") == "Clarify the tie rule" && sends.isEmpty)
        backend.transcript?("Clarify the tie rule?", true)
        voice.finishSyntheticUtterance()
        check("five-second sealed manual speech is editable draft", string(voice, "draft") == "Clarify the tie rule?" && !bool(voice, "listening") && sends.isEmpty)
        backend.transcript?("duplicate final", true)
        voice.finishSyntheticUtterance()
        check("duplicate recognizer final ignored", string(voice, "draft") == "Clarify the tie rule?" && sends.isEmpty)
        check("existing draft cannot be silently replaced by recording", voice.perform(action: "voice_listen", params: [:]) == "VOICE_DRAFT_PENDING")
        voice.perform(action: "voice_draft", params: ["text": "Should ties use the lowest ID?"])
        voice.perform(action: "voice_kind", params: ["kind": "clarify"])
        check("edited draft requires explicit send", sends.isEmpty)
        voice.perform(action: "voice_send", params: [:])
        check("existing text request receives exact edited content", sends.count == 1 && sends[0].0 == "clarify" && sends[0].1 == "Should ties use the lowest ID?")
        check("pending duplicate send rejected", voice.perform(action: "voice_send", params: [:]) == "VOICE_TURN_UNAVAILABLE" && sends.count == 1)
        check("pending draft immutable", voice.perform(action: "voice_draft", params: ["text": "altered"]) == "VOICE_TURN_UNAVAILABLE")
        voice.submissionFinished(ok: true)
        check("successful send clears draft", string(voice, "draft").isEmpty && sends.count == 1)
        voice.stop()
    }
    do {
        let (voice, backend) = fixture()
        var sends: [String] = []
        voice.onSubmit = { _, text in sends.append(text) }
        voice.perform(action: "voice_handsfree", params: ["enabled": true])
        check("handsfree opt-in alone never records", backend.listenCount == 0)
        voice.perform(action: "voice_listen", params: [:])
        let late = backend.transcript
        backend.transcript?("I will group by customer", true)
        voice.finishSyntheticUtterance()
        check("handsfree five-second seal submits once", sends == ["I will group by customer"] && !bool(voice, "listening"))
        late?("I will group by customer", true)
        check("handsfree duplicate cannot spend another request", sends.count == 1)
        voice.update(host: host(reply: 2, text: "Check the tie condition."), provider: provider(), busy: false)
        voice.submissionFinished(ok: true)
        check("backend without echo monitoring remains half duplex", bool(voice, "speaking") && !bool(voice, "listening") && backend.listenCount == 1)
        backend.finished?()
        check("explicit handsfree resumes after speech", bool(voice, "listening") && backend.listenCount == 2)
        backend.transcript?("Second plan", true)
        voice.finishSyntheticUtterance()
        voice.submissionFinished(ok: false)
        check("request failure preserves review draft and disables auto retry", sends.count == 2 && string(voice, "draft") == "Second plan" && bool(voice, "handsfree") && !bool(voice, "listening") && string(voice, "error") == "VOICE_SUBMISSION_FAILED")
        voice.submissionFinished(ok: true)
        check("late completion cannot restart failed recording", !bool(voice, "listening"))
        voice.stop()
    }
    do {
        let (voice, backend) = fixture()
        voice.perform(action: "voice_listen", params: [:])
        let stale = backend.transcript
        voice.perform(action: "voice_pause", params: [:])
        stale?("must not leak", true)
        check("pause stops actual backend and stale callback", backend.stopCount == 1 && !bool(voice, "listening") && string(voice, "draft").isEmpty)
        voice.perform(action: "voice_listen", params: [:])
        let old = backend.transcript
        voice.update(host: host("question-2"), provider: provider(), busy: false)
        old?("old question transcript", true)
        check("question transition invalidates recording and draft", !bool(voice, "listening") && string(voice, "draft").isEmpty && bool(voice, "handsfree") && bool(voice, "speaking"))
        backend.said = []
        voice.perform(action: "voice_listen", params: [:])
        let disconnected = backend.transcript
        voice.update(host: host("question-2"), provider: provider("offline"), busy: false)
        disconnected?("post disconnect", true)
        check("disconnect stops capture and invalidates callback", !bool(voice, "eligible") && !bool(voice, "listening") && string(voice, "draft").isEmpty)
        voice.update(host: host("question-2"), provider: provider(), busy: false)
        check("reconnect never resumes capture or prior speech", !bool(voice, "listening") && backend.said.isEmpty)
        voice.stop()
    }
    do {
        let (voice, backend) = fixture()
        backend.autoReady = false
        voice.perform(action: "voice_listen", params: [:])
        let permission = backend.ready
        check("permissions are explicit pending state", string(voice, "status") == "PERMISSION")
        voice.stop(); permission?()
        check("late permission grant after pause cannot record", !bool(voice, "listening") && backend.stopCount == 1)
        voice.perform(action: "voice_listen", params: [:])
        backend.failed?("VOICE_ON_DEVICE_UNAVAILABLE")
        check("device STT unavailable fails without auto fallback", string(voice, "error") == "VOICE_ON_DEVICE_UNAVAILABLE" && !bool(voice, "listening"))
        voice.stop()
    }
    do {
        let (voice, backend) = fixture()
        voice.perform(action: "voice_listen", params: [:])
        let stale = backend.transcript
        voice.update(host: host(pending: true), provider: provider(), busy: true)
        stale?("during network", true)
        check("provider wait suspends microphone", !bool(voice, "listening") && string(voice, "draft").isEmpty && string(voice, "status") == "WAITING")
        voice.update(host: host(reply: 2, text: "解释 😀 tie handling."), provider: provider(), busy: false)
        check("committed model reply only is spoken", backend.said == ["解释 😀 tie handling."] && !bool(voice, "listening"))
        backend.range?(NSRange(location: 3, length: 2))
        check("caption range uses UTF16", voice.publicState["word_start"] as? Int == 3 && voice.publicState["word_length"] as? Int == 2)
        backend.range?(NSRange(location: 500, length: 7))
        check("out of bounds caption range rejected", voice.publicState["word_start"] as? Int == 3)
        let lateSpeech = backend.finished
        voice.perform(action: "voice_mute", params: ["muted": true])
        check("speaker mute stops backend playback", !bool(voice, "speaking") && backend.speechStopCount > 0)
        let count = backend.listenCount
        lateSpeech?()
        check("late speaker completion cannot double-start mic", backend.listenCount == count)
        voice.update(host: host(reply: 3, text: "Private simulated fixture", provenance: "SIMULATED"), provider: provider(), busy: false)
        check("simulated events never spoken by live companion", backend.said.count == 1)
        voice.perform(action: "voice_mute", params: ["muted": false])
        voice.update(host: host(reply: 4, text: "Final committed reply.", canSend: false), provider: provider(), busy: false)
        check("turn limit can still play final interviewer reply", backend.said.last == "Final committed reply." && !bool(voice, "listening"))
        backend.finished?()
        check("turn limit never resumes microphone", !bool(voice, "listening"))
        check("turn limit cannot send voice", voice.perform(action: "voice_listen", params: [:]) == "VOICE_TURN_UNAVAILABLE")
        voice.stop()
    }
    do {
        let (voice, backend) = fixture()
        voice.perform(action: "voice_settings", params: ["language": "zh-CN", "rate": 0.8])
        voice.perform(action: "voice_replay", params: [:])
        check("local language and rate applied", backend.languages.last == "zh-CN" && backend.rates.last == 0.8)
        voice.update(host: host(), provider: provider(), busy: false)
        check("same committed event does not repeat playback", backend.said.count == 1)
        voice.perform(action: "voice_pause", params: [:])
        voice.perform(action: "voice_listen", params: [:])
        backend.transcript?(String(repeating: "中", count: 1366), false)
        check("recognizer output byte cap enforced", !bool(voice, "listening") && string(voice, "error") == "VOICE_TRANSCRIPT_TOO_LONG")
        voice.perform(action: "voice_clear", params: [:])
        voice.perform(action: "voice_listen", params: [:])
        voice.finishSyntheticUtterance()
        check("empty acoustic endpoint never sends or closes capture", bool(voice, "listening") && string(voice, "draft").isEmpty)
        voice.stop()
    }
    do {
        let (voice, backend) = fixture()
        voice.perform(action: "voice_listen", params: [:])
        backend.transcript?("A complete thought", false)
        RunLoop.current.run(until: Date(timeIntervalSinceNow: TIAVoiceCompanion.silenceSeconds + 0.15))
        check("silence endpoint creates a draft without paid send", !bool(voice, "listening") && string(voice, "draft") == "A complete thought")
        voice.perform(action: "voice_clear", params: [:])
        voice.perform(action: "voice_listen", params: [:])
        backend.transcript?("Half finished thought", false)
        voice.stop()
        check("focus loss clears ephemeral draft and stops capture", string(voice, "draft").isEmpty && !bool(voice, "listening"))
        voice.update(host: host(closed: true, canSend: false), provider: provider(), busy: false)
        check("closed host removes ephemeral voice data", !bool(voice, "eligible") && string(voice, "draft").isEmpty)
        voice.injectSyntheticTranscript("closed injection", final: true)
        check("native test injection obeys lifecycle", string(voice, "draft").isEmpty)
    }
    do {
        let (voice, backend) = fixture()
        voice.perform(action: "voice_replay", params: [:])
        voice.perform(action: "voice_pause", params: [:])
        check("microphone pause does not mute interviewer playback", bool(voice, "speaking"))
        backend.speechFailed?("VOICE_SPEAKER_UNAVAILABLE")
        check("missing installed voice reports typed failure", !bool(voice, "speaking") && string(voice, "error") == "VOICE_SPEAKER_UNAVAILABLE")
        voice.perform(action: "voice_mute", params: ["muted": true])
        voice.update(host: host(reply: 2, text: "A new muted reply."), provider: provider(), busy: false)
        check("muted reply still updates committed captions", string(voice, "caption") == "A new muted reply." && backend.said.count == 1)
        voice.perform(action: "voice_listen", params: [:])
        backend.transcript?("An unfinished spoken draft", false)
        voice.update(host: host(reply: 2, pending: true), provider: provider(), busy: true)
        check("typed request preserves unfinished voice draft", string(voice, "draft") == "An unfinished spoken draft" && !bool(voice, "listening") && !bool(voice, "handsfree"))
        voice.stop()
    }
    do {
        let (voice, backend) = fixture()
        voice.perform(action: "voice_replay", params: [:])
        let range = backend.range, completion = backend.finished
        voice.update(host: host(closed: true), provider: provider(), busy: false)
        range?(NSRange(location: 0, length: 7)); completion?()
        check("late speech callbacks cannot resurrect closed room", !bool(voice, "speaking") && string(voice, "caption").isEmpty && !bool(voice, "listening"))
        let production = TIAVoiceCompanion(backend: TIAVoiceMock(), testing: false)
        production.update(host: host(), provider: provider(), busy: false)
        production.perform(action: "voice_listen", params: [:])
        production.injectSyntheticTranscript("production injection", final: true)
        check("synthetic transcript entrypoint disabled outside testing", string(production, "draft").isEmpty)
        production.stop()
    }
    do {
        let (voice, _) = fixture()
        voice.perform(action: "voice_draft", params: ["text": "A guarded draft"])
        check("missing submission route returns truthful action error", voice.perform(action: "voice_send", params: [:]) == "VOICE_SUBMISSION_UNAVAILABLE")
        voice.onSubmit = { _, _ in voice.submissionFinished(ok: false) }
        check("synchronous native rejection returns action failure", voice.perform(action: "voice_send", params: [:]) == "VOICE_SUBMISSION_FAILED")
        check("rejected manual send preserves editable draft", string(voice, "draft") == "A guarded draft" && !bool(voice, "listening"))
        voice.onSubmit = nil; voice.stop()
    }
    do {
        let (voice, backend) = fixture()
        var sends = 0
        voice.onSubmit = { _, _ in sends += 1 }
        voice.perform(action: "voice_handsfree", params: ["enabled": true])
        voice.perform(action: "voice_listen", params: [:])
        backend.transcript?("A spoken plan before a real transport transition", true)
        voice.finishSyntheticUtterance()
        voice.update(host: host(pending: true, canSend: false), provider: provider("connecting", authenticated: true), busy: true)
        check("connecting retains verified room and exact pending draft", bool(voice, "eligible") && string(voice, "draft") == "A spoken plan before a real transport transition")
        check("connecting preserves handsfree consent but stops capture", bool(voice, "handsfree") && !bool(voice, "listening") && !bool(voice, "can_listen") && string(voice, "status") == "WAITING")
        voice.submissionFinished(ok: true)
        voice.update(host: host(reply: 2, text: "A committed response after connecting."), provider: provider(), busy: false)
        check("real connecting-to-commit transition preserves automatic speech", backend.said == ["A committed response after connecting."] && bool(voice, "speaking"))
        backend.finished?()
        check("handsfree resumes after verified response finishes", bool(voice, "listening") && backend.listenCount == 2)
        backend.transcript?("Retryable second draft", true)
        voice.finishSyntheticUtterance()
        voice.update(host: host(reply: 2, pending: true, canSend: false), provider: provider("connecting", authenticated: true), busy: true)
        voice.submissionFinished(ok: false)
        voice.update(host: host(reply: 2), provider: provider("unavailable", authenticated: true), busy: false)
        check("recoverable unavailable preserves editable voice draft", bool(voice, "eligible") && string(voice, "draft") == "Retryable second draft" && string(voice, "error") == "VOICE_SUBMISSION_FAILED")
        check("unavailable stops auto submit and new recording", sends == 2 && bool(voice, "handsfree") && !bool(voice, "listening") && voice.perform(action: "voice_listen", params: [:]) == "VOICE_TURN_UNAVAILABLE")
        voice.update(host: host(reply: 2), provider: provider("unavailable", authenticated: false), busy: false)
        check("invalid credential still clears all ephemeral voice data", !bool(voice, "eligible") && string(voice, "draft").isEmpty && bool(voice, "handsfree"))
        voice.onSubmit = nil; voice.stop()
    }
    do {
        let backend = TIAVoiceMock()
        let voice = TIAVoiceCompanion(backend: backend)
        var sends = 0
        voice.onSubmit = { _, _ in sends += 1 }
        voice.update(host: host(), provider: provider(), busy: false)
        check("fresh entry enables handsfree and speaks committed introduction", bool(voice, "handsfree") && bool(voice, "speaking") && backend.said.count == 1)
        backend.finished?()
        check("entry starts listening after introduction", bool(voice, "listening") && backend.listenCount == 1)
        backend.transcript?("My clarification", true)
        voice.finishSyntheticUtterance()
        check("default five-second sealed speech sends exactly once", sends == 1)
        voice.submissionFinished(ok: true)
        voice.perform(action: "voice_pause", params: [:])
        voice.update(host: host(), provider: provider(), busy: false)
        check("snapshot never reverses manual pause", !bool(voice, "listening") && bool(voice, "handsfree"))
        voice.update(host: host("question-2"), provider: provider(), busy: false)
        check("new question resets automatic mode", bool(voice, "handsfree") && bool(voice, "speaking"))
        backend.finished?()
        backend.failed?("VOICE_MIC_PERMISSION_DENIED")
        voice.update(host: host("question-2"), provider: provider(), busy: false)
        check("permission failure never retries on snapshot", !bool(voice, "listening") && bool(voice, "handsfree"))
        voice.stop()
    }
    do {
        let gate = TIAVoiceActivationGate()
        var starts = 0
        gate.wait(active: false) { starts += 1 }
        check("permission grant while inactive waits for foreground", starts == 0)
        gate.becameActive(); gate.becameActive()
        check("foreground after permission starts exactly once", starts == 1)
        gate.wait(active: false) { starts += 1 }; gate.cancel(); gate.becameActive()
        check("pause cancels deferred permission activation", starts == 1)
        gate.wait(active: true) { starts += 1 }
        check("already active permission starts immediately", starts == 2)
        let backend = TIAVoiceMock(); backend.autoReady = false
        let voice = TIAVoiceCompanion(backend: backend)
        voice.update(host: host(), provider: provider(), busy: false); backend.finished?()
        check("permission pending preserves automatic preference", voice.isAwaitingPermission && bool(voice, "handsfree"))
        backend.ready?()
        check("permission completion continues automatic listening", bool(voice, "listening") && bool(voice, "handsfree"))
        voice.stop()
        check("external interruption stops audio without changing preference", !bool(voice, "listening") && bool(voice, "handsfree"))
        voice.perform(action: "voice_listen", params: [:]); backend.ready?()
        check("listen resumes automatic mode after interruption", bool(voice, "listening") && bool(voice, "handsfree"))
        voice.stop()
    }
    do {
        var gate = TIAVoiceSilenceGate()
        check("no acoustic evidence cannot seal", !gate.maySeal(at: 100))
        gate.observe(10)
        check("five-second minimum is exact", !gate.maySeal(at: 14.999) && gate.maySeal(at: 15))
        gate.observe(14.9)
        check("resumed candidate speech resets acoustic deadline", !gate.maySeal(at: 19.899) && gate.maySeal(at: 19.9))
        gate.observe(13); gate.observe(.nan)
        check("late or invalid activity cannot move deadline backwards", gate.lastActivity == 14.9)
        check("monotonic backward sample fails closed", !gate.maySeal(at: 2))
    }
    do {
        let (voice, backend) = fixture()
        var sends = [String]()
        voice.onSubmit = { _, text in sends.append(text) }
        voice.perform(action: "voice_handsfree", params: ["enabled": true])
        voice.perform(action: "voice_listen", params: [:])
        backend.transcript?("I am still explaining", true)
        check("recognizer early final never sends or stops listening", sends.isEmpty && bool(voice, "listening"))
        voice.advanceSyntheticTime(by: 4.8)
        check("under five seconds cannot seal finalized recognition", sends.isEmpty)
        voice.injectSyntheticActivity()
        voice.advanceSyntheticTime(by: 4.8)
        check("actual speech resets deadline even with unchanged transcript", sends.isEmpty && bool(voice, "listening"))
        voice.advanceSyntheticTime(by: 0.3)
        check("five uninterrupted acoustic seconds submit once", sends == ["I am still explaining"])
        voice.advanceSyntheticTime(by: 10)
        backend.transcript?("late duplicate final", true)
        check("duplicate final and stale timer cannot resubmit", sends.count == 1)
        voice.stop()
    }
    do {
        let backend = TIAVoiceMock(); backend.canMonitorDuringPlayback = true
        let voice = TIAVoiceCompanion(backend: backend)
        var sent = [(String, String)]()
        voice.onSubmit = { sent.append(($0, $1)) }
        voice.update(host: host(), provider: provider(), busy: false)
        check("granted permission keeps echo-cancelled detector on during playback",
              bool(voice, "speaking") && bool(voice, "listening") && bool(voice, "barge_in_monitoring"))
        let oldFinish = backend.finished
        let stops = backend.speechStopCount
        backend.activity?(ProcessInfo.processInfo.systemUptime, false)
        backend.rawTranscript?("Explain your plan.", true)
        voice.advanceSyntheticTime(by: 5)
        check("playback-only recognition cannot seal candidate text", sent.isEmpty && string(voice, "partial").isEmpty)
        check("unconfirmed impulse does not interrupt interviewer playback", bool(voice, "speaking"))
        voice.injectSyntheticActivity()
        check("candidate acoustic onset stops playback before text arrives",
              !bool(voice, "speaking") && bool(voice, "listening") && backend.speechStopCount == stops + 1)
        voice.injectSyntheticTranscript("Skip the introduction and read the question", final: true)
        check("barge-in recognition final alone cannot send", sent.isEmpty)
        voice.finishSyntheticUtterance()
        check("introduction interruption remains ordinary candidate dialogue",
              sent.count == 1 && sent[0].0 == "clarify" && sent[0].1 == "Skip the introduction and read the question")
        oldFinish?()
        check("interrupted speech completion cannot restart capture", !bool(voice, "listening"))
        voice.stop()
    }
    do {
        var detector = TIACandidateSpeechDetector()
        let silence = [Float](repeating: 0, count: 1024)
        var impulse = silence; impulse[20] = 0.8
        check("echo-cancelled silence cannot produce candidate onset", !silence.withUnsafeBufferPointer { detector.observe(samples: $0, sampleRate: 48000) })
        check("isolated keyboard impulse cannot produce candidate onset", !impulse.withUnsafeBufferPointer { detector.observe(samples: $0, sampleRate: 48000) })
        var active = false
        for block in 0..<8 {
            let radiansPerSample: Double = 2.0 * Double.pi * 200.0 / 48000.0
            let speechBand: [Float] = (0..<1024).map { sample in
                let phase = radiansPerSample * Double(block * 1024 + sample)
                return Float(0.1 * sin(phase))
            }
            active = speechBand.withUnsafeBufferPointer { detector.observe(samples: $0, sampleRate: 48000) } || active
        }
        check("sustained post-AEC voice-band activity reaches onset detector", active)
    }
    do {
        let format = AVAudioFormat(standardFormatWithSampleRate: 48000, channels: 1)!
        func frame(_ value: Float) -> AVAudioPCMBuffer {
            let result = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: 1024)!
            result.frameLength = 1024
            for index in 0..<1024 { result.floatChannelData![0][index] = value }
            return result
        }
        var delivered = [Float]()
        let pipe = TIARecognitionPipe(syntheticSink: { delivered.append($0.floatChannelData![0][0]) })
        pipe.guardPlayback(true)
        for _ in 0..<100 { pipe.append(frame(0.1), candidateOnset: false) }
        check("interviewer playback never enters cumulative recognizer text", delivered.isEmpty)
        for _ in 0..<8 { pipe.append(frame(0.4), candidateOnset: false) }
        pipe.append(frame(0.4), candidateOnset: true)
        check("candidate onset preserves bounded first syllable only", !delivered.isEmpty && delivered.count <= 8 && delivered.allSatisfy { $0 == 0.4 })
        pipe.append(frame(0.5), candidateOnset: false)
        check("recognition continues after candidate interrupts playback", delivered.last == 0.5)
        delivered = []; pipe.guardPlayback(true)
        pipe.append(frame(0.1), candidateOnset: false)
        pipe.guardPlayback(false)
        pipe.append(frame(0.7), candidateOnset: false)
        check("normal playback completion discards retained echo frames", delivered == [0.7])
        delivered = []; pipe.guardPlayback(true)
        pipe.append(frame(0.1), candidateOnset: false); pipe.replace(nil)
        pipe.append(frame(0.8), candidateOnset: false)
        check("capture cancellation wipes playback pre-roll", delivered == [0.8])
    }
    print("Voice tests: \(checks - failures) passed, \(failures) failed; microphone captures: 0; synthesized audio: 0; provider requests: 0")
    return failures == 0 ? 0 : 1
}
