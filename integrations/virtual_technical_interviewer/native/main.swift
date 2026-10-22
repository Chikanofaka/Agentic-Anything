import AppKit
import WebKit
import UniformTypeIdentifiers

final class TIAApp: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate, WKUIDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var worker: TIAWorker?
    private var indexURL: URL!
    lazy var portal: NativePortal = {
        // Every automated App run uses a fail-closed mock URLProtocol, including
        // the older tutorial tests. No test flag can spend a real credential.
        NativePortal(adapter: TIAOpenAIAdapter(configuration: uiTesting ? TIATestHTTPProtocol.configuration() : .ephemeral))
    }()
    private var busy = false
    private var seenIDs = Set<String>()
    private var lastState: [String: Any] = [:]
    private var portalSheet: NSAlert?
    private var smoke: TIAUISmoke?
    let uiTesting = CommandLine.arguments.contains("--ui-self-test") || CommandLine.arguments.contains("--ui-recovery-test") || CommandLine.arguments.contains("--ui-setup-test") || CommandLine.arguments.contains("--ui-live-test") || CommandLine.arguments.contains("--ui-live-recovery-test") || CommandLine.arguments.contains("--ui-provider-failure-test")
    private var liveRequestID: String?
    private var liveGeneration: String?
    private var liveStage = "idle"
    private var cancellationIDs = [String]()
    private var loaded = false
    private var dataDirectory: URL!
    private var smokeDirectory: URL!

    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            guard let resources = Bundle.main.resourceURL else { throw CocoaError(.fileNoSuchFile) }
            indexURL = resources.appendingPathComponent("ui/index.html").standardizedFileURL
            for name in ["index.html", "app.js", "style.css"] {
                guard FileManager.default.isReadableFile(atPath: resources.appendingPathComponent("ui/" + name).path)
                else { throw CocoaError(.fileNoSuchFile) }
            }
            if uiTesting {
                TIATestHTTPProtocol.reset(CommandLine.arguments.contains("--ui-live-test") ? [
                    .reply("Before choosing a query, explain how you will handle tied timestamps and NULL dates.", usage: ["input_tokens": 120, "output_tokens": 24, "total_tokens": 144]),
                    .reply("State your own diagnosis first. Which edge case will you check next?", usage: ["input_tokens": 150, "output_tokens": 18, "total_tokens": 168])
                ] : [])
                if CommandLine.arguments.contains("--ui-provider-failure-test") {
                    var delayed = TIATestHTTPProtocol.Plan.reply("This cancelled mock response must never commit.")
                    delayed.delay = 1
                    TIATestHTTPProtocol.reset([
                        .init(status: 401, payload: Data("{}".utf8)),
                        .init(payload: Data(), error: .timedOut),
                        .reply("Please clarify how ties should be resolved."), delayed,
                        .reply("Explain your own diagnosis before asking for another hint.")
                    ])
                }
                // Optional output location is native argv, never a renderer parameter.
                if let i = CommandLine.arguments.firstIndex(of: "--test-output"), CommandLine.arguments.count > i + 1 {
                    smokeDirectory = URL(fileURLWithPath: CommandLine.arguments[i + 1], isDirectory: true)
                } else {
                    smokeDirectory = FileManager.default.temporaryDirectory.appendingPathComponent("tia-ui-" + UUID().uuidString)
                }
                dataDirectory = smokeDirectory.appendingPathComponent("synthetic-data")
            } else {
                dataDirectory = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
                    .appendingPathComponent("Technical Interview Lab", isDirectory: true)
            }
            worker = try TIAWorker(runtime: resources.appendingPathComponent("runtime"), dataDirectory: dataDirectory)
            worker?.onFailure = { [weak self] in
                guard let self = self else { return }
                self.portal.disconnect()
                self.finishLive(ok: false, error: "LOCAL_CONTROLLER_UNAVAILABLE")
                self.busy = false
                self.emit(["ok": false, "state": self.lastState, "error": "LOCAL_CONTROLLER_UNAVAILABLE"])
            }
            let config = WKWebViewConfiguration()
            config.websiteDataStore = .nonPersistent()
            config.preferences.javaScriptCanOpenWindowsAutomatically = false
            config.userContentController.add(self, name: "tia")
            webView = WKWebView(frame: NSRect(x: 0, y: 0, width: 1120, height: 820), configuration: config)
            webView.navigationDelegate = self
            webView.uiDelegate = self
            webView.allowsBackForwardNavigationGestures = false
            window = NSWindow(contentRect: webView.frame, styleMask: [.titled, .closable, .miniaturizable, .resizable],
                              backing: .buffered, defer: false)
            window.title = "Technical Interview Lab · TIA"
            window.minSize = NSSize(width: 720, height: 600)
            window.contentView = webView
            window.center()
            window.makeKeyAndOrderFront(nil)
            installMenu()
            webView.loadFileURL(indexURL, allowingReadAccessTo: resources.appendingPathComponent("ui"))
            NSApp.activate(ignoringOtherApps: true)
            DispatchQueue.main.asyncAfter(deadline: .now() + 12) { [weak self] in
                guard let self = self else { return }
                self.webView.evaluateJavaScript("document.documentElement.dataset.tiaReady === 'true'") { result, error in
                    if error != nil || result as? Bool != true || !self.loaded { self.failure("The local interview screen could not start. Rebuild the app and restart.") }
                }
            }
        } catch { failure("The local controller could not start. This development build requires /usr/bin/python3.") }
    }

    private func installMenu() {
        let menu = NSMenu()
        let app = NSMenuItem(); menu.addItem(app); app.submenu = NSMenu()
        app.submenu?.addItem(withTitle: "Quit Technical Interview Lab", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        let edit = NSMenuItem(); menu.addItem(edit); edit.submenu = NSMenu(title: "Edit")
        edit.submenu?.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
        edit.submenu?.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        edit.submenu?.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        edit.submenu?.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        edit.submenu?.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        NSApp.mainMenu = menu
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationWillTerminate(_ notification: Notification) { portal.disconnect(); worker?.stop() }

    func failure(_ message: String) {
        portal.disconnect()
        if uiTesting { print("FAIL native UI startup"); exit(4) }
        let alert = NSAlert(); alert.messageText = "Technical Interview Lab"; alert.informativeText = message
        alert.runModal(); NSApp.terminate(nil)
    }
    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        let url = action.request.url?.standardizedFileURL
        let main = action.targetFrame?.isMainFrame ?? (action.navigationType == .other)
        decisionHandler(main && BridgePolicy.allowedDocument(url, entry: indexURL) ? .allow : .cancel)
    }
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? { nil }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        failure("The bundled screen did not load.")
    }
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        failure("The bundled screen did not load.")
    }
    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) { failure("The screen process stopped. Restart to recover saved progress.") }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        loaded = true
        guard uiTesting, smoke == nil else { return }
        smoke = TIAUISmoke(app: self, directory: smokeDirectory) { [weak self] code in
            self?.portal.disconnect(); self?.worker?.stop()
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) { exit(code) }
        }
        smoke?.run()
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "tia", message.frameInfo.isMainFrame,
              BridgePolicy.allowedDocument(message.frameInfo.request.url, entry: indexURL),
              let (id, action, params) = BridgePolicy.validate(message.body) else {
            emit(["ok": false, "error": "INVALID_BRIDGE_REQUEST"]); return
        }
        guard seenIDs.count < 10000, seenIDs.insert(id).inserted else {
            emit(["id": id, "ok": false, "error": "DUPLICATE_OR_EXHAUSTED_REQUEST"]); return
        }
        // Cancellation remains available while a paid request is pending. The
        // renderer can request cancellation but cannot call prepare/commit itself.
        if action == "disconnect" || action == "preview_cancel" {
            cancelLive(id: id, disconnect: action == "disconnect"); return
        }
        guard !busy, portalSheet == nil else { emit(["id": id, "ok": false, "error": "NATIVE_BUSY"]); return }
        if action == "api_portal" {
            guard ["API_PORTAL", "LIVE_PREVIEW", "REVIEW"].contains(lastState["screen"] as? String ?? "") else { emit(["id": id, "ok": false, "error": "INVALID_TRANSITION"]); return }
            openPortal { self.respondWithState(id) }; return
        }
        if action == "preview_verify" || action == "preview_send" {
            beginLive(id: id, action: action, params: params); return
        }
        if action == "reset" || action == "tutorial_replay" {
            confirm(action == "reset" ? "Delete the local tutorial save and transcript?" : "Replace this tutorial with a fresh rehearsal? Export first if you want to keep it.") { confirmed in
                if confirmed { self.portal.disconnect(); self.forward(id: id, action: action, params: params) }
                else { self.respondWithState(id) }
            }
            return
        }
        forward(id: id, action: action, params: params)
    }

    private func forward(id: String, action: String, params: [String: Any]) {
        busy = true
        worker?.request(action, params: params) { [weak self] reply in
            guard let self = self else { return }
            self.busy = false
            var result = reply; result["id"] = id
            if let state = result["state"] as? [String: Any] { self.lastState = state }
            if result["ok"] as? Bool == true, action == "export" {
                // Export is initiated by the user in a native Save panel. The renderer
                // never supplies filesystem paths, and personal transcripts aren't logged.
                self.exportReceipt(result) { status in
                    var response = result
                    response["exported"] = status == "EXPORTED"
                    if status == "FAILED" { response["ok"] = false; response["error"] = "EXPORT_FAILED" }
                    self.emit(response)
                }
                return
            }
            if result["ok"] as? Bool == true, action == "choose_real" {
                self.emit(result)
                self.openPortal { self.emit(["ok": true, "state": self.lastState]) }
                return
            }
            self.emit(result)
        }
    }

    private func beginLive(id: String, action: String, params: [String: Any]) {
        guard portal.publicState["live_enabled"] as? Bool == true else {
            emit(["id": id, "ok": false, "state": lastState, "error": "PAID_CONSENT_REQUIRED"]); return
        }
        if action == "preview_send", portal.publicState["authenticated"] as? Bool != true {
            emit(["id": id, "ok": false, "state": lastState, "error": "PROVIDER_AUTHENTICATION_REQUIRED"]); return
        }
        let preview = lastState["live_preview"] as? [String: Any]
        let config = lastState["setup_config"] as? [String: Any]
        let currentMechanism = preview?["closed"] as? Bool == false ? preview?["mechanism"] as? String : nil
        let mechanism = currentMechanism ?? config?["interviewer_mechanism"] as? String ?? "STRICT_CHALLENGING"
        let generation = portal.generation
        let requestID = UUID().uuidString
        busy = true; liveRequestID = id; liveGeneration = generation; liveStage = "preparing"
        let preparedParams: [String: Any] = [
            "request_id": requestID, "generation": generation,
            "operation": action == "preview_verify" ? "verify" : "reply",
            "text": params["text"] as? String ?? "", "kind": params["kind"] as? String ?? "clarify",
            "mechanism": mechanism
        ]
        worker?.request("native_prepare_preview", params: preparedParams) { [weak self] response in
            guard let self = self else { return }
            if let state = response["state"] as? [String: Any] { self.lastState = state }
            guard self.liveGeneration == self.portal.generation else { self.cancelPrepared(error: "REQUEST_CANCELLED"); return }
            guard response["ok"] as? Bool == true,
                  let prepared = response["prepared"] as? [String: Any],
                  let spec = try? TIAModelRequest(prepared), spec.generation == generation,
                  spec.requestID == requestID else {
                self.cancelPrepared(error: response["error"] as? String ?? "INVALID_PREPARED_REQUEST"); return
            }
            self.liveStage = "calling"
            self.portal.send(spec) { [weak self] result in
                guard let self = self, self.liveStage == "calling",
                      self.liveGeneration == generation, self.portal.generation == generation else { return }
                switch result {
                case .failure(let failure): self.cancelPrepared(error: failure.code)
                case .success(let reply):
                    // Linearization point: only this native callback may authorize
                    // commit, after checking the same activation generation again.
                    self.liveStage = "committing"
                    let commitment: [String: Any] = [
                        "transaction_id": spec.transactionID, "request_id": requestID,
                        "generation": generation, "reply": ["reply": reply.text],
                        "model": self.portal.publicState["model"] as? String ?? "",
                        "usage": reply.usage as Any? ?? NSNull()
                    ]
                    self.worker?.request("native_commit_preview", params: commitment) { [weak self] committed in
                        guard let self = self else { return }
                        if let state = committed["state"] as? [String: Any] { self.lastState = state }
                        self.finishLive(ok: committed["ok"] as? Bool == true,
                                        error: committed["error"] as? String)
                    }
                }
            }
            // Unsolicited status contains no request instructions or credentials.
            self.emit(["ok": true, "state": self.lastState])
        }
    }

    private func cancelLive(id: String, disconnect: Bool) {
        if disconnect { portal.disconnect() } else { portal.cancel() }
        if disconnect, let sheet = portalSheet, portalIsVisible {
            window.endSheet(sheet.window, returnCode: .alertSecondButtonReturn)
        }
        guard liveRequestID != nil else { respondWithState(id); return }
        if liveStage == "committing" {
            // A controller commitment already submitted is atomic. Disconnect still
            // clears the credential immediately; never claim this saved turn rolled back.
            emit(["id": id, "ok": disconnect, "state": lastState,
                  "error": "COMMIT_ALREADY_SUBMITTED"]); return
        }
        cancellationIDs.append(id)
        if liveStage == "calling" { cancelPrepared(error: "REQUEST_CANCELLED") }
        // During preparation the Worker callback runs first, then cancels its
        // transaction. Never send two concurrent requests to the serial Worker.
    }

    private func cancelPrepared(error: String) {
        guard liveStage != "cancelling" else { return }
        liveStage = "cancelling"
        worker?.request("native_cancel_preview") { [weak self] response in
            guard let self = self else { return }
            if let state = response["state"] as? [String: Any] { self.lastState = state }
            self.finishLive(ok: false, error: error)
        }
    }

    private func finishLive(ok: Bool, error: String?) {
        guard let id = liveRequestID else { return }
        liveRequestID = nil; liveGeneration = nil; liveStage = "idle"; busy = false
        var result: [String: Any] = ["id": id, "ok": ok, "state": lastState]
        if let error = error { result["error"] = error }
        emit(result)
        let cancelled = cancellationIDs; cancellationIDs.removeAll()
        for cancellation in cancelled { respondWithState(cancellation) }
    }

    private func respondWithState(_ id: String) { emit(["id": id, "ok": true, "state": lastState]) }
    func emit(_ raw: [String: Any]) {
        var result = raw
        if var state = result["state"] as? [String: Any] {
            state["activation"] = portal.publicState
            if portal.publicState["authenticated"] as? Bool == true,
               let blockers = state["setup_blockers"] as? [String] {
                state["setup_blockers"] = blockers.filter { $0 != "PROVIDER_AUTHENTICATION_REQUIRED" }
            }
            if uiTesting { state["transport_mode"] = "MOCK_HTTP" }
            result["state"] = state
        }
        guard JSONSerialization.isValidJSONObject(result),
              let bytes = try? JSONSerialization.data(withJSONObject: result),
              bytes.count <= TIAWorker.maximumResponseBytes else { return }
        // Base64 avoids script interpolation of any candidate text.
        let b64 = bytes.base64EncodedString()
        webView?.evaluateJavaScript("window.tiaReceive(JSON.parse(new TextDecoder().decode(Uint8Array.from(atob('\(b64)'),c=>c.charCodeAt(0)))))", completionHandler: nil)
    }

    private func confirm(_ text: String, completion: @escaping (Bool) -> Void) {
        let alert = NSAlert(); alert.messageText = "Local data / 本机数据"; alert.informativeText = text
        alert.addButton(withTitle: "Confirm / 确认"); alert.addButton(withTitle: "Cancel / 取消")
        portalSheet = alert
        alert.beginSheetModal(for: window) { [weak self] response in
            self?.portalSheet = nil; completion(response == .alertFirstButtonReturn)
        }
    }

    func openPortal(completion: @escaping () -> Void) {
        let alert = NSAlert()
        alert.messageText = "API Portal · OpenAI"
        alert.informativeText = """
        Native secure input · 原生安全输入
        Your key stays in native memory until Disconnect or Quit. Activation makes no request and is UNVERIFIED until a valid response.
        Only https://api.openai.com/v1/responses is used. Each Verify or Send uses at most one paid request, 600 output tokens, 30 seconds. No retries or redirects. The selected request cap is not a currency budget. Model prices and provider retention policies apply.
        Requests send the approved role instructions, your selected tutorial or imported question (statement, schema, input/output examples and constraints), and conversation context including your submitted text to OpenAI. Review private BYOQ content before authorizing. No SQL execution or scores. Cancelled requests may still be billed.
        密钥仅留在原生内存；授权不发送请求。请求会发送所选题目（含自带题目的题干、表结构、输入输出示例及约束）和对话内容；授权前请检查私有内容。验证或发送每次最多调用一次，可能收费；取消后仍可能计费。预览不执行 SQL，也不评分。
        """
        alert.addButton(withTitle: "Allow bounded requests / 授权有限请求")
        alert.addButton(withTitle: "Cancel / 取消")
        let container = NSView(frame: NSRect(x: 0, y: 0, width: 460, height: 180))
        let field = NSSecureTextField(frame: NSRect(x: 0, y: 146, width: 460, height: 26))
        field.placeholderString = "API key (session only)"; field.setAccessibilityLabel("Session-only API key")
        let modelLabel = NSTextField(labelWithString: "Model / 模型")
        modelLabel.frame = NSRect(x: 0, y: 111, width: 120, height: 22)
        let model = NSTextField(frame: NSRect(x: 130, y: 106, width: 330, height: 26))
        model.stringValue = "gpt-4.1-mini"; model.setAccessibilityLabel("OpenAI model identifier")
        let limitLabel = NSTextField(labelWithString: "Request cap / 请求上限")
        limitLabel.frame = NSRect(x: 0, y: 74, width: 220, height: 22)
        let limit = NSPopUpButton(frame: NSRect(x: 260, y: 68, width: 200, height: 28))
        limit.addItems(withTitles: ["1", "2", "5", "10", "20"]); limit.selectItem(withTitle: "2")
        limit.setAccessibilityLabel("Maximum paid requests per activation")
        let consent = NSButton(checkboxWithTitle: "I consent to paid requests / 我同意付费请求", target: nil, action: nil)
        consent.frame = NSRect(x: 0, y: 22, width: 460, height: 24)
        for view in [field, modelLabel, model, limitLabel, limit, consent] { container.addSubview(view) }
        alert.accessoryView = container
        alert.buttons[0].isEnabled = false
        let delegate = CredentialFieldDelegate { [weak alert, weak field, weak model, weak consent] in
            alert?.buttons[0].isEnabled = NativePortal.validCredential(field?.stringValue ?? "") &&
                (model?.stringValue.range(of: "\\A[A-Za-z0-9][A-Za-z0-9._-]{0,79}\\z", options: .regularExpression) != nil) && consent?.state == .on
        }
        field.delegate = delegate; model.delegate = delegate
        consent.target = delegate; consent.action = #selector(CredentialFieldDelegate.changed)
        portalSheet = alert
        alert.beginSheetModal(for: window) { [weak self] result in
            guard let self = self else { return }
            _ = delegate // Retain for the sheet's entire lifetime.
            if result == .alertFirstButtonReturn {
                _ = self.portal.activate(key: field.stringValue, model: model.stringValue,
                                        requestLimit: Int(limit.titleOfSelectedItem ?? "") ?? 0,
                                        paidConsent: consent.state == .on)
            }
            field.stringValue = ""; consent.state = .off
            self.portalSheet = nil; completion()
        }
        alert.window.makeFirstResponder(field)
    }

    // Test fixture input is synthetic and all automated HTTP is intercepted.
    var portalIsVisible: Bool { portalSheet?.messageText == "API Portal · OpenAI" }
    func cancelPortalForTest() {
        guard uiTesting, let alert = portalSheet else { return }
        window.endSheet(alert.window, returnCode: .alertSecondButtonReturn)
    }
    func enterSyntheticCredentialForTest() -> Bool {
        guard uiTesting, let alert = portalSheet, portalIsVisible,
              let field = alert.accessoryView?.subviews.compactMap({ $0 as? NSSecureTextField }).first,
              let consent = alert.accessoryView?.subviews.compactMap({ $0 as? NSButton }).first(where: { !($0 is NSPopUpButton) }),
              let delegate = field.delegate as? CredentialFieldDelegate else { return false }
        field.stringValue = "synthetic-ui-fixture-not-a-real-key"
        if CommandLine.arguments.contains("--ui-provider-failure-test") {
            alert.accessoryView?.subviews.compactMap({ $0 as? NSPopUpButton }).first?.selectItem(withTitle: "5")
        }
        consent.state = .on; delegate.changed()
        guard alert.buttons[0].isEnabled else { return false }
        window.endSheet(alert.window, returnCode: .alertFirstButtonReturn)
        return true
    }
    private func exportReceipt(_ result: [String: Any], completion: @escaping (String) -> Void) {
        guard var exported = (result["export"] ?? result["record"]) as? [String: Any] else {
            completion("FAILED"); return
        }
        if exported["live_preview"] != nil {
            // Native-only provider facts decorate the export; frozen controller
            // receipts and their hashes are never rewritten.
            exported["native_provider_at_export"] = portal.publicState
            if uiTesting { exported["transport_mode"] = "MOCK_HTTP" }
            if portal.publicState["authenticated"] as? Bool == true,
               var setup = exported["setup"] as? [String: Any], let blockers = setup["blockers"] as? [String] {
                setup["blockers"] = blockers.filter { $0 != "PROVIDER_AUTHENTICATION_REQUIRED" }
                exported["setup"] = setup
            }
        }
        guard
              JSONSerialization.isValidJSONObject(exported),
              let data = try? JSONSerialization.data(withJSONObject: exported, options: [.prettyPrinted, .sortedKeys]) else {
            completion("FAILED"); return
        }
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.json]; panel.nameFieldStringValue = "tia-tutorial-receipt.json"
        panel.message = "Includes your submitted text. Choose where to keep this private export."
        panel.beginSheetModal(for: window) { result in
            guard result == .OK, let url = panel.url else { completion("CANCELLED"); return }
            do {
                try PrivateExport.write(data, to: url)
                completion("EXPORTED")
            } catch { completion("FAILED") }
        }
    }
}

final class CredentialFieldDelegate: NSObject, NSTextFieldDelegate {
    private let callback: () -> Void
    init(_ callback: @escaping () -> Void) { self.callback = callback }
    @objc func changed() { callback() }
    func controlTextDidChange(_ obj: Notification) { callback() }
}

if CommandLine.arguments.contains("--self-test") {
    let core = runNativeTests()
    let provider = runProviderTests()
    exit(core == 0 && provider == 0 ? 0 : 1)
}
let application = NSApplication.shared
application.setActivationPolicy(.regular)
let delegate = TIAApp()
application.delegate = delegate
application.run()
