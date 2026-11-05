import AppKit
import WebKit
import Foundation
import Darwin

// Separately linked audio laboratory. No Worker, NativePortal, provider adapter,
// database, interview receipt, or credential code is linked into this executable.
final class TIAAudioLabJournal {
    static let cases = ["permissions", "microphone", "transcription", "silence", "silence_reset", "early_final", "exactly_once", "barge_in", "echo", "manual_input", "pause", "mute_replay", "language", "drag", "focus", "recovery", "export", "stop_isolation"]
    let runID = UUID().uuidString
    let mode: String
    private let started = ProcessInfo.processInfo.systemUptime
    private(set) var events = [[String: Any]]()
    private(set) var feedback = [String: [String: Any]]()
    private(set) var sequence = 0
    private(set) var dropped = 0
    init(synthetic: Bool) { mode = synthetic ? "SYNTHETIC" : "REAL_LOCAL_AUDIO" }
    func record(_ event: String, _ details: [String: Any] = [:]) {
        // Reject accidental payload-bearing metadata rather than logging speech.
        let prohibited = ["text", "transcript", "draft", "partial", "caption", "key", "audio", "path"]
        var safe = [String: Any]()
        for (key, value) in details.prefix(24) where !prohibited.contains(where: { key.lowercased().contains($0) }) || key.hasSuffix("_bytes") {
            if let value = value as? String { safe[String(key.prefix(64))] = String(value.prefix(160)) }
            else if let value = value as? NSNumber, value.doubleValue.isFinite { safe[String(key.prefix(64))] = value }
        }
        sequence += 1
        events.append(["sequence": sequence, "elapsed_seconds": (ProcessInfo.processInfo.systemUptime - started), "event": String(event.prefix(80)), "details": safe])
        if events.count > 2000 { events.removeFirst(); dropped += 1 }
    }
    func mark(_ payload: [String: Any]) -> Bool {
        guard Set(payload.keys) == ["case_id", "result", "note"], let id = payload["case_id"] as? String,
              Self.cases.contains(id), let result = payload["result"] as? String,
              ["PASS", "FAIL", "NOT_RUN", "BLOCKED"].contains(result), let note = payload["note"] as? String, note.utf8.count <= 2000 else { return false }
        feedback[id] = ["case_id": id, "result": result, "note": note]
        record("HUMAN_FEEDBACK", ["case_id": id, "result": result]); return true
    }
    var checklist: [[String: Any]] { Self.cases.map { feedback[$0] ?? ["case_id": $0, "result": "NOT_RUN", "note": ""] } }
    var report: [String: Any] {
        ["schema": "tia-audio-uat/v1", "run_id": runID, "mode": mode, "events": events,
         "events_dropped": dropped, "feedback": checklist, "provider_requests": 0,
         "reply_source": "SCRIPTED_LOCAL", "raw_audio_saved": false, "transcript_saved": false,
         "interview_state_accessed": false, "hardware_acceptance": mode == "SYNTHETIC" ? "NOT_RUN" : "HUMAN_CHECKLIST_REQUIRED",
         "os_version": ProcessInfo.processInfo.operatingSystemVersionString]
    }
}

// Restrict every write to a new per-run directory. Reject symlinked parents and
// use 0600 no-follow creation; the report contains deliberate human notes only.
final class TIAAudioLabReport {
    let directory: URL
    var url: URL { directory.appendingPathComponent("report.json") }
    init(root: URL, runID: String) throws {
        directory = root.appendingPathComponent(runID, isDirectory: true).standardizedFileURL
        try Self.validateParents(directory)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: directory.path)
    }
    private static func validateParents(_ url: URL) throws {
        var current = url
        while current.path != "/" {
            if let attr = try? FileManager.default.attributesOfItem(atPath: current.path),
               attr[.type] as? FileAttributeType != .typeDirectory { throw CocoaError(.fileWriteInvalidFileName) }
            current.deleteLastPathComponent()
        }
    }
    func write(_ report: [String: Any]) throws {
        try Self.validateParents(directory)
        let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
        let temporary = directory.appendingPathComponent(".report-" + UUID().uuidString)
        let fd = Darwin.open(temporary.path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0o600)
        guard fd >= 0 else { throw CocoaError(.fileWriteUnknown) }
        var complete = false
        defer { Darwin.close(fd); if !complete { Darwin.unlink(temporary.path) } }
        try data.withUnsafeBytes { buffer in
            var offset = 0
            while offset < buffer.count {
                let count = Darwin.write(fd, buffer.baseAddress!.advanced(by: offset), buffer.count - offset)
                if count < 0 && errno == EINTR { continue }
                guard count > 0 else { throw CocoaError(.fileWriteUnknown) }
                offset += count
            }
        }
        guard fsync(fd) == 0, Darwin.rename(temporary.path, url.path) == 0 else { throw CocoaError(.fileWriteUnknown) }
        complete = true
    }
    static func export(_ report: [String: Any], to destination: URL) throws {
        let target = destination.standardizedFileURL
        try validateParents(target.deletingLastPathComponent())
        if let attributes = try? FileManager.default.attributesOfItem(atPath: target.path),
           attributes[.type] as? FileAttributeType != .typeRegular {
            throw CocoaError(.fileWriteInvalidFileName)
        }
        let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
        let temporary = target.deletingLastPathComponent().appendingPathComponent(".tia-audio-export-" + UUID().uuidString)
        let fd = Darwin.open(temporary.path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0o600)
        guard fd >= 0 else { throw CocoaError(.fileWriteUnknown) }
        var complete = false
        defer { Darwin.close(fd); if !complete { Darwin.unlink(temporary.path) } }
        try data.withUnsafeBytes { buffer in
            var offset = 0
            while offset < buffer.count {
                let count = Darwin.write(fd, buffer.baseAddress!.advanced(by: offset), buffer.count - offset)
                if count < 0 && errno == EINTR { continue }
                guard count > 0 else { throw CocoaError(.fileWriteUnknown) }
                offset += count
            }
        }
        guard fsync(fd) == 0, Darwin.rename(temporary.path, target.path) == 0 else {
            throw CocoaError(.fileWriteUnknown)
        }
        complete = true
        try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: target.path)
    }
}

// Automated laboratory checks never construct a real microphone/speech backend.
final class TIAAudioLabSyntheticBackend: TIAVoiceBackend {
    var canMonitorDuringPlayback: Bool { true }
    private var speechGeneration = UUID()
    func listen(language: String, ready: @escaping () -> Void, activity: @escaping (TimeInterval, Bool) -> Void,
                transcript: @escaping (String, Bool) -> Void, failed: @escaping (String) -> Void) { ready() }
    func stopListening() {}
    func speak(_ text: String, language: String, rate: Double, range: @escaping (NSRange) -> Void,
               finished: @escaping () -> Void, failed: @escaping (String) -> Void) {
        speechGeneration = UUID(); let token = speechGeneration
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) { [weak self] in
            guard self?.speechGeneration == token else { return }
            range(NSRange(location: 0, length: (text as NSString).length)); finished()
        }
    }
    func stopSpeaking() { speechGeneration = UUID() }
}

final class TIAAudioLabApp: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate {
    private var window: NSWindow!
    private var web: WKWebView!
    private var page: URL!
    private var loaded = false
    private let synthetic: Bool
    private let journal: TIAAudioLabJournal
    private var reportFile: TIAAudioLabReport?
    private let voice: TIAVoiceCompanion
    private var running = false, busy = false
    private var epoch = UUID(), sessionID = UUID().uuidString
    private var replyID: String?, replyText = ""
    private var turns = [[String: Any]]()
    private var candidateTurns = 0
    private var uiTimer: Timer?
    private var lastSave = 0.0
    private var outputError: String?
    private var exportedPath: String?
    private var seenIDs = Set<String>()
    private var smokeStep = 0, smokePassed = [String](), smokeDeadline = 0.0
    private var smokeEvaluating = false

    init(synthetic: Bool) {
        self.synthetic = synthetic; journal = TIAAudioLabJournal(synthetic: synthetic)
        voice = TIAVoiceCompanion(backend: synthetic ? TIAAudioLabSyntheticBackend() : TIALocalVoiceBackend(), testing: synthetic, localAudioUAT: true)
        super.init()
        voice.onDiagnostic = { [weak self] event, fields in self?.journal.record(event, fields) }
        voice.onChange = { [weak self] _ in self?.render() }
        voice.onSubmit = { [weak self] kind, text in self?.accept(kind: kind, text: text) }
    }
    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            let args = CommandLine.arguments
            let root: URL
            if let index = args.firstIndex(of: "--report-root"), args.indices.contains(index + 1), args[index + 1].hasPrefix("/") {
                root = URL(fileURLWithPath: args[index + 1], isDirectory: true)
            } else {
                root = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("TIA Audio Lab/runs")
            }
            reportFile = try TIAAudioLabReport(root: root, runID: journal.runID)
            guard let resources = Bundle.main.resourceURL else { throw CocoaError(.fileNoSuchFile) }
            page = resources.appendingPathComponent("ui/audio-uat.html").standardizedFileURL
            guard FileManager.default.isReadableFile(atPath: page.path) else { throw CocoaError(.fileReadNoSuchFile) }
            let config = WKWebViewConfiguration()
            config.websiteDataStore = .nonPersistent()
            config.userContentController.add(self, name: "audioUAT")
            web = WKWebView(frame: .zero, configuration: config); web.navigationDelegate = self
            window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1200, height: 850), styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
            window.title = synthetic ? "TIA Audio Lab · SYNTHETIC AUTOMATION" : "TIA Audio Lab · Local microphone · Scripted replies"
            window.contentView = web; window.center(); window.makeKeyAndOrderFront(nil)
            NSApplication.shared.activate(ignoringOtherApps: true)
            web.loadFileURL(page, allowingReadAccessTo: page.deletingLastPathComponent())
            journal.record("LAB_STARTED", ["mode": journal.mode, "reply_source": "SCRIPTED_LOCAL"])
            save()
            print("Audio UAT report: \(reportFile!.url.path)")
            uiTimer = Timer.scheduledTimer(withTimeInterval: 0.25, repeats: true) { [weak self] _ in
                guard let self else { return }
                self.render()
                if ProcessInfo.processInfo.systemUptime - self.lastSave >= 1 { self.save() }
                if self.synthetic && self.loaded { self.smokeTick() }
            }
            smokeDeadline = ProcessInfo.processInfo.systemUptime + 60
        } catch { fputs("AUDIO_UAT_START_FAILED\n", stderr); NSApplication.shared.terminate(nil) }
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationWillResignActive(_ notification: Notification) {
        guard running, !voice.isAwaitingPermission else { return }
        // Preserve words for typing after a focus interruption; never auto-resume
        // capture on return. This is the same explicit pause action as the widget.
        _ = voice.perform(action: "voice_pause", params: [:])
        _ = voice.perform(action: "voice_mute", params: ["muted": true])
        journal.record("APP_INACTIVE_PAUSED"); render(); save()
    }
    func applicationWillTerminate(_ notification: Notification) { stop(); save() }
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        decisionHandler(navigationAction.request.url?.standardizedFileURL == page && navigationAction.targetFrame?.isMainFrame == true ? .allow : .cancel)
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) { loaded = true; render() }
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.frameInfo.isMainFrame, message.frameInfo.request.url?.standardizedFileURL == page,
              let body = message.body as? [String: Any], Set(body.keys) == ["id", "action", "payload"],
              let id = body["id"] as? String, !id.isEmpty, id.utf8.count <= 80,
              let action = body["action"] as? String, let payload = body["payload"] as? [String: Any],
              let bytes = try? JSONSerialization.data(withJSONObject: body), bytes.count <= 12288 else { return }
        guard !seenIDs.contains(id), seenIDs.count < 20000 else { respond(id, error: "AUDIO_UAT_DUPLICATE_OR_LIMIT"); return }
        seenIDs.insert(id)
        if action == "export_report" {
            exportReport(id: id, payload: payload)
            return
        }
        let error = command(action, payload)
        if let error { journal.record("ACTION_REJECTED", ["action": action, "code": error]) }
        render(); respond(id, error: error); save()
    }
    private func command(_ action: String, _ payload: [String: Any]) -> String? {
        if action.hasPrefix("voice_") {
            guard TIAVoiceCompanion.validate(action: action, params: payload) else { return "VOICE_INVALID_ACTION" }
            journal.record("UI_ACTION", ["action": action])
            return voice.perform(action: action, params: payload)
        }
        switch action {
        case "begin":
            guard payload.isEmpty else { return "AUDIO_UAT_INVALID_PAYLOAD" }
            guard !running else { return nil }
            epoch = UUID(); sessionID = UUID().uuidString; running = true; busy = false
            replyID = UUID().uuidString
            replyText = "This is the local audio test. No AI service is connected. Say a short sentence, then stay quiet for five seconds. You can interrupt this introduction by speaking."
            if voice.publicState["language"] as? String == "zh-CN" { replyText = "这是本地语音测试，没有连接人工智能服务。请说一句话，然后保持安静五秒钟。你也可以讲话来打断这段介绍。" }
            turns = [["role": "interviewer", "text": replyText, "kind": "scripted"]]; candidateTurns = 0
            journal.record("ROUND_STARTED"); updateVoice(); return nil
        case "stop": guard payload.isEmpty else { return "AUDIO_UAT_INVALID_PAYLOAD" }; stop(); return nil
        case "feedback": return journal.mark(payload) ? nil : "AUDIO_UAT_INVALID_FEEDBACK"
        default: return "AUDIO_UAT_ACTION_NOT_ALLOWED"
        }
    }
    private func exportReport(id: String, payload: [String: Any]) {
        guard payload.isEmpty else { respond(id, error: "AUDIO_UAT_INVALID_PAYLOAD"); return }
        save()
        guard outputError == nil, let reportFile else { respond(id, error: outputError ?? "AUDIO_UAT_EXPORT_FAILED"); return }
        if synthetic {
            completeExport(id: id, destination: reportFile.directory.appendingPathComponent("exported-report.json"), reveal: false)
            return
        }
        let panel = NSSavePanel()
        panel.title = "Export TIA Audio Lab diagnostic report"
        panel.prompt = "Export"
        panel.nameFieldStringValue = "tia-audio-uat-\(journal.runID).json"
        panel.allowedContentTypes = [.json]
        panel.canCreateDirectories = true
        panel.directoryURL = FileManager.default.urls(for: .downloadsDirectory, in: .userDomainMask).first
        // The bridge reply stays pending while the user chooses a destination;
        // the App and WebKit main thread remain responsive.
        panel.beginSheetModal(for: window) { [weak self] response in
            guard let self else { return }
            guard response == .OK, let destination = panel.url else {
                self.respond(id, error: "AUDIO_UAT_EXPORT_CANCELLED")
                return
            }
            self.completeExport(id: id, destination: destination, reveal: true)
        }
    }
    private func completeExport(id: String, destination: URL, reveal: Bool) {
        do {
            try TIAAudioLabReport.export(journal.report, to: destination)
            exportedPath = destination.standardizedFileURL.path
            let bytes = (try? Data(contentsOf: destination).count) ?? 0
            journal.record("REPORT_EXPORTED", ["bytes": bytes])
            save(); render(); respond(id, error: nil)
            if reveal { NSWorkspace.shared.activateFileViewerSelecting([destination]) }
        } catch {
            outputError = "AUDIO_UAT_EXPORT_FAILED"
            journal.record("REPORT_EXPORT_FAILED", ["code": outputError!])
            render(); respond(id, error: outputError); save()
        }
    }
    private func stop() {
        epoch = UUID(); running = false; busy = false; voice.stop(); updateVoice()
        turns.removeAll(); journal.record("ROUND_STOPPED"); render()
    }
    private func updateVoice() {
        voice.updateLocalAudioUAT(sessionID: sessionID, replyID: replyID, replyText: replyText, active: running, busy: busy)
    }
    private func accept(kind: String, text: String) {
        guard running, !busy, !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { voice.submissionFinished(ok: false); return }
        busy = true; candidateTurns += 1; let token = epoch
        turns.append(["role": "candidate", "text": text, "kind": kind])
        if turns.count > 40 { turns.removeFirst(turns.count - 40) }
        journal.record("LOCAL_TURN_ACCEPTED", ["turn": candidateTurns, "kind": kind, "transcript_bytes": text.utf8.count])
        updateVoice()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) { [weak self] in
            guard let self, self.running, self.epoch == token else { return }
            self.busy = false; self.replyID = UUID().uuidString
            let chinese = self.voice.publicState["language"] as? String == "zh-CN"
            let skipIntro = text.lowercased().contains("skip") && (text.lowercased().contains("intro") || text.lowercased().contains("read the question")) || text.contains("跳过介绍")
            self.replyText = skipIntro
                ? (chinese ? "测试问题是：请描述你最喜欢的一道菜。这只跳过了介绍，没有切换面试题。" : "The practice question is: describe a favourite meal. Only the introduction was skipped; no interview question was advanced.")
                : (chinese ? "已在本机收到第\(self.candidateTurns)段发言。请继续说话，或者测试暂停和编辑草稿。这是脚本回复。" : "Local turn \(self.candidateTurns) received. Try another sentence, or test pause and edit draft. This response is scripted.")
            self.turns.append(["role": "interviewer", "text": self.replyText, "kind": "scripted"])
            self.journal.record("SCRIPTED_REPLY_READY", ["turn": self.candidateTurns])
            // Clear successful draft while still in busy context, then present
            // the reply so capture cannot briefly restart between these steps.
            self.voice.submissionFinished(ok: true); self.updateVoice(); self.save()
        }
    }
    private var snapshot: [String: Any] {
        ["running": running, "pending": busy, "voice": voice.publicState, "events": journal.events,
         "turns": turns, "candidate_turns": candidateTurns, "mode": journal.mode, "run_id": journal.runID,
         "feedback": journal.checklist, "report_path": reportFile?.url.path ?? "", "session_id": sessionID,
         "exported_path": exportedPath as Any? ?? NSNull(),
         "error": outputError as Any? ?? NSNull()]
    }
    private func render() {
        guard loaded else { return }
        sendJS("window.TIAAudioUAT.update", snapshot)
    }
    private func respond(_ id: String, error: String?) {
        sendJS("window.TIAAudioUAT.receive", ["id": id, "ok": error == nil,
                                               "error": error as Any? ?? NSNull(),
                                               "report_path": reportFile?.url.path ?? "",
                                               "exported_path": exportedPath as Any? ?? NSNull()])
    }
    private func sendJS(_ function: String, _ value: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]), let json = String(data: data, encoding: .utf8) else { return }
        // JSON is data passed to a fixed JS function; no evaluated user source.
        web.evaluateJavaScript(function + "(" + json + ")", completionHandler: nil)
    }
    private func save() {
        lastSave = ProcessInfo.processInfo.systemUptime
        do { try reportFile?.write(journal.report); outputError = nil }
        catch { outputError = "AUDIO_UAT_REPORT_WRITE_FAILED" }
    }
    private func smokeTick() {
        if ProcessInfo.processInfo.systemUptime > smokeDeadline { finishSmoke(false, "TIMEOUT_STEP_\(smokeStep)"); return }
        guard !smokeEvaluating else { return }
        switch smokeStep {
        case 0: smokeJS("!!window.TIAAudioUAT && !!window.TIAVoice", "WebKit laboratory loaded") { self.smokeJSCommand("begin"); self.smokeStep = 1 }
        case 1:
            guard voice.publicState["listening"] as? Bool == true else { return }
            smokePassed.append("Synthetic microphone ready; no physical capture")
            voice.injectSyntheticTranscript("synthetic candidate phrase", final: true)
            voice.advanceSyntheticTime(by: 4.5)
            guard candidateTurns == 0 else { finishSmoke(false, "EARLY_SEND"); return }
            smokePassed.append("Recognizer final does not send before five seconds")
            voice.injectSyntheticActivity(); voice.advanceSyntheticTime(by: 4.5)
            guard candidateTurns == 0 else { finishSmoke(false, "SILENCE_NOT_RESET"); return }
            voice.advanceSyntheticTime(by: 0.6); voice.finishSyntheticUtterance(); smokeStep = 2
        case 2:
            guard candidateTurns == 1, !busy, voice.publicState["listening"] as? Bool == true else { return }
            smokePassed.append("Five-second reset, exactly-one local delivery and scripted reply")
            smokeJSCommand("voice_pause"); smokeStep = 3
        case 3:
            guard voice.publicState["listening"] as? Bool == false else { return }
            smokeJS("(()=>{document.getElementById('voiceToggle').click(); const d=document.getElementById('voiceDraft'); d.value='manual synthetic phrase'; d.dispatchEvent(new Event('input',{bubbles:true})); return !d.readOnly && !d.disabled;})()", "Manual draft is editable") { self.smokeStep = 4 }
        case 4:
            smokeJS("(()=>{const b=document.getElementById('voiceSend'); if(b.disabled)return false; b.click(); return true;})()", "Send uses actual widget event handlers") { self.smokeStep = 5 }
        case 5:
            guard candidateTurns == 2, !busy else { return }
            smokePassed.append("Typed local turn and second reply complete")
            smokeJSCommand("stop"); smokeStep = 6
        case 6:
            guard !running else { return }
            voice.injectSyntheticTranscript("late synthetic callback", final: true); voice.finishSyntheticUtterance()
            guard candidateTurns == 2 else { finishSmoke(false, "STALE_COMMIT"); return }
            smokePassed.append("Stopped lab rejects late callbacks")
            smokeJSCommand("export_report"); smokeStep = 7
        default:
            guard outputError == nil, let reportFile, FileManager.default.fileExists(atPath: reportFile.url.path) else { finishSmoke(false, "EXPORT_FAILED"); return }
            smokePassed.append("Private metadata report saved")
            finishSmoke(true, nil)
        }
    }
    private func smokeJSCommand(_ action: String) {
        web.evaluateJavaScript("window.TIAAudioUAT.command('\(action)',{}).then(()=>true)", completionHandler: nil)
    }
    private func smokeJS(_ script: String, _ name: String, next: @escaping () -> Void) {
        smokeEvaluating = true
        web.evaluateJavaScript(script) { [weak self] value, error in
            guard let self else { return }; self.smokeEvaluating = false
            if error == nil, value as? Bool == true { self.smokePassed.append(name); next() }
        }
    }
    private func finishSmoke(_ ok: Bool, _ error: String?) {
        uiTimer?.invalidate(); stop()
        var receipt = journal.report
        receipt["status"] = ok ? "PASSED" : "FAILED"; receipt["checks"] = smokePassed
        receipt["failure"] = error as Any? ?? NSNull(); receipt["microphone_captures"] = 0; receipt["real_provider_requests"] = 0
        try? reportFile?.write(receipt)
        print("AUDIO_UAT_WEBKIT \(ok ? "PASSED" : "FAILED"): \(smokePassed.count) checks \(error ?? "")")
        // Avoid willTerminate overwriting the receipt.
        fflush(stdout); exit(ok ? 0 : 1)
    }
}

func runAudioLabTests() -> Int32 {
    var checks = 0, failures = 0
    func check(_ name: String, _ value: Bool) { checks += 1; if !value { failures += 1; print("FAIL audio-lab: \(name)") } }
    let journal = TIAAudioLabJournal(synthetic: true)
    journal.record("TEST", ["text": "do not save", "api_key": "do not save", "transcript_bytes": 4, "count": 1])
    let fields = journal.events[0]["details"] as! [String: Any]
    check("no raw speech or secret-shaped details", fields["text"] == nil && fields["api_key"] == nil && fields["transcript_bytes"] as? Int == 4)
    for _ in 0..<2001 { journal.record("FRAME") }
    check("bounded chronological ring", journal.events.count == 2000 && journal.dropped == 2 && journal.events.first?["sequence"] as? Int == 3)
    check("human results start not run", journal.checklist.allSatisfy { $0["result"] as? String == "NOT_RUN" })
    check("reject invented case", !journal.mark(["case_id": "invented", "result": "PASS", "note": ""]))
    check("reject overlong feedback", !journal.mark(["case_id": "silence", "result": "FAIL", "note": String(repeating: "a", count: 2001)]))
    check("accept explicit human failure", journal.mark(["case_id": "silence", "result": "FAIL", "note": "synthetic feedback"] ))
    check("no fabricated hardware acceptance", journal.report["hardware_acceptance"] as? String == "NOT_RUN")
    // Use the canonical directory rather than macOS's /var compatibility
    // symlink; the report writer deliberately rejects symlinked parents.
    let root = URL(fileURLWithPath: "/private/tmp", isDirectory: true)
        .appendingPathComponent("tia-audio-journal-tests-" + UUID().uuidString)
    do {
        let report = try TIAAudioLabReport(root: root, runID: "run")
        try report.write(journal.report)
        let attr = try FileManager.default.attributesOfItem(atPath: report.url.path)
        check("private file permissions", attr[.posixPermissions] as? Int == 0o600)
        let decoded = try JSONSerialization.jsonObject(with: Data(contentsOf: report.url)) as! [String: Any]
        check("export is metadata only", decoded["transcript_saved"] as? Bool == false && decoded["provider_requests"] as? Int == 0)
        let exported = root.appendingPathComponent("exported.json")
        try TIAAudioLabReport.export(journal.report, to: exported)
        check("export creates a selected artifact", FileManager.default.fileExists(atPath: exported.path))
        let exportedAttributes = try FileManager.default.attributesOfItem(atPath: exported.path)
        check("exported artifact is private", exportedAttributes[.posixPermissions] as? Int == 0o600)
        let link = root.appendingPathComponent("link")
        try FileManager.default.createSymbolicLink(at: link, withDestinationURL: report.directory)
        do { _ = try TIAAudioLabReport(root: link, runID: "blocked"); check("symlink parents blocked", false) }
        catch { check("symlink parents blocked", true) }
        try FileManager.default.removeItem(at: root)
    } catch { check("report write", false) }
    print("Audio lab tests: \(checks - failures)/\(checks) passed; no microphone or provider requests")
    return failures == 0 ? 0 : 1
}
