import AppKit
import WebKit
import UniformTypeIdentifiers

let replySchema: [String: Any] = ["type": "object", "properties": ["reply": ["type": "string"]], "required": ["reply"], "additionalProperties": false]

struct BridgePolicy {
    static let actions: Set<String> = ["snapshot", "start", "preview_turn", "turn", "continue", "inspect", "approach", "language", "advance", "link", "verdict", "forget", "reset", "export", "activate", "disconnect", "cancel", "developer"]
    static func validate(_ body: Any) -> (String, String, [String: Any])? {
        guard let object = body as? [String: Any], Set(object.keys) == ["id", "action", "params"],
              let id = object["id"] as? String, id.count <= 64, !id.isEmpty,
              id.range(of: "\\A[A-Za-z0-9_-]+\\z", options: .regularExpression) != nil,
              let action = object["action"] as? String, actions.contains(action),
              let params = object["params"] as? [String: Any],
              JSONSerialization.isValidJSONObject(object),
              let data = try? JSONSerialization.data(withJSONObject: object), data.count <= 16384 else { return nil }
        let expected: Set<String>
        switch action {
        case "start": expected = params["language"] == nil ? ["player", "style"] : ["player", "style", "language"]
        case "preview_turn": expected = ["text"]
        case "turn": expected = ["text", "confirm_case"]
        case "link": expected = ["clues"]
        case "inspect": expected = ["id"]
        case "language": expected = ["language"]
        default: expected = []
        }
        guard Set(params.keys) == expected else { return nil }
        if action == "turn" || action == "preview_turn" {
            guard let text = params["text"] as? String, !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty, text.count <= 1000 else { return nil }
        }
        if action == "turn" {
            guard let number = params["confirm_case"] as? NSNumber, CFGetTypeID(number) == CFBooleanGetTypeID() else { return nil }
        }
        if action == "inspect" {
            guard let id = params["id"] as? String, id.range(of: "\\A[a-z][a-z0-9_]{0,31}\\z", options: .regularExpression) != nil else { return nil }
        }
        if action == "language" || params["language"] != nil {
            guard let language = params["language"] as? String, ["zh", "en"].contains(language) else { return nil }
        }
        return (id, action, params)
    }
}

final class AppController: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate, WKUIDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var worker: CoreWorker?
    var indexURL: URL!
    private let uiSelfTest = CommandLine.arguments.contains("--ui-self-test")
    private var uiSmoke: OfflineUISmoke?
    private var uiScreenshotURL: URL?
    private var credential: String?
    private var model = "gpt-4.1-mini"
    private var verified = false
    private var requestsUsed = 0
    private var busy = false
    private var corePending = false
    private var committing = false
    private var generation = 0
    private var activeUIID: String?
    private var pendingTransaction: String?
    private var activationSheet = false
    private var seenIDs = Set<String>()
    private var pendingCaseProposal: (text: String, topic: String)?
    private let adapter = OpenAIAdapter()

    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            guard let resources = Bundle.main.resourceURL,
                  let configData = try? Data(contentsOf: resources.appendingPathComponent("config.json")),
                  let config = try JSONSerialization.jsonObject(with: configData) as? [String: String],
                  let projectRoot = config["project_root"] else { throw ProviderFailure.invalidConfiguration }
            indexURL = resources.appendingPathComponent("ui/index.html").standardizedFileURL
            if uiSelfTest { uiScreenshotURL = URL(fileURLWithPath: projectRoot).appendingPathComponent("integrations/witness_loop/.build-cache/v03-ui-smoke-" + UUID().uuidString) }
            let dataPath = uiSelfTest ? "integrations/witness_loop/.build-cache/ui-self-test-" + UUID().uuidString : "integrations/witness_loop/data"
            worker = try CoreWorker(runtime: resources.appendingPathComponent("runtime"), dataDirectory: URL(fileURLWithPath: projectRoot).appendingPathComponent(dataPath))
            worker?.onFailure = { [weak self] in
                guard let self = self else { return }
                self.adapter.cancel(); self.credential = nil; self.verified = false
                self.generation += 1; self.busy = false
                self.emit(id: nil, ok: false, error: "The local Core is unavailable. Close and restart the app.")
            }
            let configuration = WKWebViewConfiguration()
            configuration.websiteDataStore = .nonPersistent()
            configuration.preferences.javaScriptCanOpenWindowsAutomatically = false
            configuration.userContentController.add(self, name: "hal")
            webView = WKWebView(frame: NSRect(x: 0, y: 0, width: 1180, height: 820), configuration: configuration)
            webView.navigationDelegate = self
            webView.uiDelegate = self
            webView.allowsBackForwardNavigationGestures = false
            window = NSWindow(contentRect: webView.frame, styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
            window.title = "Witness Loop · HAL · v0.3"
            window.minSize = NSSize(width: 800, height: 620)
            window.contentView = webView
            window.center(); window.makeKeyAndOrderFront(nil)
            webView.loadFileURL(indexURL, allowingReadAccessTo: resources.appendingPathComponent("ui"))
            installMenu()
            NSApp.activate(ignoringOtherApps: true)
        } catch {
            let alert = NSAlert()
            alert.messageText = "The HAL local app could not start."
            alert.informativeText = "Rebuild using scripts/build_witness_mac.sh and check that /usr/bin/python3 and the local Core are available."
            alert.runModal(); NSApp.terminate(nil)
        }
    }

    private func installMenu() {
        let menu = NSMenu()
        let app = NSMenuItem(); menu.addItem(app)
        let appMenu = NSMenu(); app.submenu = appMenu
        appMenu.addItem(withTitle: "Quit Witness Loop", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        let edit = NSMenuItem(); menu.addItem(edit)
        let editMenu = NSMenu(title: "Edit"); edit.submenu = editMenu
        editMenu.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        NSApp.mainMenu = menu
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationWillTerminate(_ notification: Notification) { adapter.cancel(); credential = nil; worker?.stop() }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        decisionHandler(navigationAction.targetFrame?.isMainFrame == true && navigationAction.request.url?.standardizedFileURL == indexURL ? .allow : .cancel)
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        guard uiSelfTest, uiSmoke == nil else { return }
        uiSmoke = OfflineUISmoke(webView: webView, screenshotURL: uiScreenshotURL!) { [weak self] code in
            self?.worker?.stop()
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) { exit(code) }
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in self?.uiSmoke?.run() }
    }
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration, for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? { nil }

    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        guard frame.isMainFrame, frame.request.url?.standardizedFileURL == indexURL, !activationSheet, !busy, message.count <= 2000 else { completionHandler(false); return }
        activationSheet = true
        let alert = NSAlert()
        alert.messageText = "Confirm local action"
        alert.informativeText = message
        alert.addButton(withTitle: "Confirm")
        alert.addButton(withTitle: "Cancel")
        alert.beginSheetModal(for: window) { [weak self] response in
            self?.activationSheet = false
            completionHandler(response == .alertFirstButtonReturn)
        }
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "hal", message.frameInfo.isMainFrame,
              message.frameInfo.request.url?.standardizedFileURL == indexURL,
              let (id, action, params) = BridgePolicy.validate(message.body) else { return }
        guard !seenIDs.contains(id), seenIDs.count < 10000 else { emit(id: id, ok: false, error: "Duplicate request or session limit. Restart the app."); return }
        seenIDs.insert(id)
        if !["turn", "preview_turn", "snapshot"].contains(action) { pendingCaseProposal = nil }
        if action == "cancel" || action == "disconnect" {
            let error = cancelCurrent(disconnect: action == "disconnect")
            emit(id: id, ok: error == nil, error: error); return
        }
        guard !busy, !activationSheet else { emit(id: id, ok: false, error: "A turn or native prompt is already in progress."); return }
        if action == "activate" {
            guard !uiSelfTest else { emit(id: id, ok: false, error: "Activation is disabled in offline UI self-test mode."); return }
            showActivation(id: id); return
        }
        if action == "turn" { runTurn(id: id, text: params["text"] as! String, confirmCase: params["confirm_case"] as! Bool); return }
        busy = true
        coreRequest(action, params: params) { [weak self] envelope in
            guard let self = self else { return }
            self.busy = false
            if action == "export", envelope["ok"] as? Bool == true, let result = envelope["result"] as? [String: Any] { self.saveExport(id: id, result: result) }
            else { self.forward(envelope, id: id) }
        }
    }

    private func coreRequest(_ action: String, params: [String: Any] = [:], completion: @escaping ([String: Any]) -> Void) {
        corePending = true
        guard let worker = worker else { corePending = false; completion(["ok": false, "error": "The local Core is unavailable."]); return }
        worker.request(action, params: params) { [weak self] envelope in
            self?.corePending = false
            completion(envelope)
        }
    }

    private var activation: [String: Any] {
        ["state": credential == nil ? "OFFLINE" : (verified ? "LIVE_VERIFIED" : "ACTIVATED_UNVERIFIED"), "provider": "openai", "model": model, "requests_used": requestsUsed, "request_limit": 20, "busy": busy]
    }

    private func emit(id: String?, ok: Bool = true, result: [String: Any] = [:], error: String? = nil) {
        var data = result
        data["activation"] = activation
        var envelope: [String: Any] = ["id": id as Any? ?? NSNull(), "ok": ok, "result": data]
        if let error = error { envelope["error"] = error }
        guard let encoded = try? JSONSerialization.data(withJSONObject: envelope, options: [.sortedKeys]), let raw = String(data: encoded, encoding: .utf8) else { return }
        let literal = raw.replacingOccurrences(of: "\u{2028}", with: "\\u2028").replacingOccurrences(of: "\u{2029}", with: "\\u2029")
        webView?.evaluateJavaScript("window.halReceive && window.halReceive(\(literal));", completionHandler: nil)
    }

    private func forward(_ envelope: [String: Any], id: String) {
        if envelope["ok"] as? Bool == true { emit(id: id, result: envelope["result"] as? [String: Any] ?? [:]) }
        else { emit(id: id, ok: false, error: envelope["error"] as? String ?? "The local Core rejected this action.") }
    }

    private func showActivation(id: String) {
        activationSheet = true
        let alert = NSAlert()
        alert.messageText = "Activate OpenAI for this session"
        alert.informativeText = "Your key stays in native app memory until Disconnect or Quit. It never enters this game page, the Python Core, or a saved file.\n\nOnly https://api.openai.com/v1/responses is used. Each game turn sends the bounded persona, clues, selected memories and your message; it can use 2 paid requests. Maximum 20 requests per activation, 200 classifier / 600 reply output tokens, 30 seconds each. No automatic retries or redirects. Your provider may retain request data under its own policies.\n\nActivation makes no network call. The first successful response verifies access. Click Allow to consent to these requests when you play; this is a request cap, not a currency budget."
        alert.addButton(withTitle: "Allow session requests")
        alert.addButton(withTitle: "Cancel")
        let view = NSView(frame: NSRect(x: 0, y: 0, width: 440, height: 108))
        let keyLabel = NSTextField(labelWithString: "API key (native secure field)"); keyLabel.frame = NSRect(x: 0, y: 82, width: 440, height: 20); view.addSubview(keyLabel)
        let keyField = NSSecureTextField(frame: NSRect(x: 0, y: 52, width: 440, height: 26)); keyField.placeholderString = "Paste directly here, never into chat"; view.addSubview(keyField)
        let modelLabel = NSTextField(labelWithString: "Model"); modelLabel.frame = NSRect(x: 0, y: 6, width: 50, height: 24); view.addSubview(modelLabel)
        let modelField = NSTextField(frame: NSRect(x: 60, y: 4, width: 380, height: 26)); modelField.stringValue = model; view.addSubview(modelField)
        alert.accessoryView = view
        alert.beginSheetModal(for: window) { [weak self] response in
            guard let self = self else { keyField.stringValue = ""; return }
            self.activationSheet = false
            defer { keyField.stringValue = "" }
            guard response == .alertFirstButtonReturn else { self.emit(id: id, result: [:]); return }
            let key = keyField.stringValue
            let chosenModel = modelField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
            do { _ = try OpenAIAdapter.request(key: key, model: chosenModel, spec: ModelRequest(instructions: "Validate configuration only", input: [:], schema: replySchema, name: "hal_reply", outputTokens: 600)) }
            catch { self.emit(id: id, ok: false, error: "Enter a nonempty credential with no spaces/newlines and a valid model name."); return }
            self.credential = key; self.model = chosenModel; self.verified = false; self.requestsUsed = 0; self.generation += 1
            self.emit(id: id, result: [:])
        }
        window.makeFirstResponder(keyField)
    }

    private func runTurn(id: String, text: String, confirmCase: Bool) {
        let retainedTopic = confirmCase && pendingCaseProposal?.text == text ? pendingCaseProposal?.topic : nil
        let requiredRequests = retainedTopic == nil ? 2 : 1
        guard credential == nil || requestsUsed <= 20 - requiredRequests else { emit(id: id, ok: false, error: "This activation has insufficient requests left for this turn. Disconnect or explicitly activate a new session."); return }
        busy = true; activeUIID = id; pendingTransaction = nil
        generation += 1
        let token = generation
        emit(id: nil, result: [:])
        if credential == nil { prepare(id: id, text: text, topic: nil, confirmCase: confirmCase, token: token); return }
        if let topic = retainedTopic {
            pendingCaseProposal = nil
            prepare(id: id, text: text, topic: topic, confirmCase: true, token: token)
            return
        }
        // Core validates phase, remaining actions and explicit case confirmation
        // before the first billable request. It checks again after classification.
        coreRequest("classify_context", params: ["text": text, "confirm_case": confirmCase]) { [weak self] envelope in
            guard let self = self else { return }
            guard token == self.generation else { self.busy = false; self.emit(id: nil); return }
            guard envelope["ok"] as? Bool == true, let context = envelope["result"] as? [String: Any],
                  let instructions = context["instructions"] as? String, let input = context["input"],
                  let suppliedSchema = context["schema"] as? [String: Any],
                  let properties = suppliedSchema["properties"] as? [String: Any],
                  let topicProperty = properties["topic"] as? [String: Any],
                  let topics = topicProperty["enum"] as? [String], !topics.isEmpty, topics.count <= 32,
                  topics.allSatisfy({ !$0.isEmpty && $0.count <= 64 }) else {
                self.failTurn(id: id, message: envelope["error"] as? String ?? "The domain could not prepare topic classification.", token: token); return
            }
            let topicSchema: [String: Any] = ["type": "object", "properties": ["topic": ["type": "string", "enum": topics]], "required": ["topic"], "additionalProperties": false]
            self.modelCall(ModelRequest(instructions: instructions, input: input, schema: topicSchema, name: "hal_topic", outputTokens: 200), token: token) { result in
                switch result {
                case .failure(let failure): self.failTurn(id: id, message: failure.publicMessage, token: token)
                case .success(let object):
                    guard Set(object.keys) == ["topic"], let topic = object["topic"] as? String, topics.contains(topic) else {
                        self.failTurn(id: id, message: "The topic response did not match the domain contract.", token: token); return
                    }
                    self.verified = true
                    self.prepare(id: id, text: text, topic: topic, confirmCase: confirmCase, token: token)
                }
            }
        }
    }

    private func prepare(id: String, text: String, topic: String?, confirmCase: Bool, token: Int) {
        var params: [String: Any] = ["text": text, "confirm_case": confirmCase]
        if let topic = topic { params["topic"] = topic }
        coreRequest("prepare_turn", params: params) { [weak self] envelope in
            guard let self = self else { return }
            guard token == self.generation else {
                if envelope["ok"] as? Bool == true {
                    self.coreRequest("cancel_turn") { _ in self.busy = false; self.emit(id: nil) }
                } else { self.busy = false; self.emit(id: nil) }
                return
            }
            guard envelope["ok"] as? Bool == true, let result = envelope["result"] as? [String: Any], let transaction = result["transaction_id"] as? String else {
                if envelope["error"] as? String == "CASE_ACTION_CONFIRMATION_REQUIRED", let topic = topic {
                    // Keep only this proposed topic until explicit confirmation;
                    // no second classification charge for the identical message.
                    self.pendingCaseProposal = (text, topic)
                } else { self.pendingCaseProposal = nil }
                self.failTurn(id: id, message: envelope["error"] as? String ?? "The domain could not prepare this turn.", token: token); return
            }
            self.pendingTransaction = transaction
            if self.credential == nil {
                guard let reply = result["fallback_reply"] as? String else { self.failTurn(id: id, message: "The offline reply was unavailable.", token: token); return }
                self.commit(id: id, transaction: transaction, reply: reply, mode: "SIMULATED", token: token); return
            }
            guard let context = result["context"] as? [String: Any], let instructions = context["instructions"] as? String, let input = context["input"] else {
                self.failTurn(id: id, message: "The domain reply context was invalid.", token: token); return
            }
            self.modelCall(ModelRequest(instructions: instructions, input: input, schema: replySchema, name: "hal_reply", outputTokens: 600), token: token) { result in
                switch result {
                case .failure(let failure): self.failTurn(id: id, message: failure.publicMessage, token: token)
                case .success(let object):
                    guard Set(object.keys) == ["reply"], let reply = object["reply"] as? String, !reply.isEmpty, reply.count <= 4000 else {
                        self.failTurn(id: id, message: "The character response did not match the domain contract.", token: token); return
                    }
                    self.commit(id: id, transaction: transaction, reply: reply, mode: "LIVE_MODEL", token: token)
                }
            }
        }
    }

    private func modelCall(_ spec: ModelRequest, token: Int, completion: @escaping (Result<[String: Any], ProviderFailure>) -> Void) {
        guard token == generation, let key = credential, requestsUsed < 20 else { completion(.failure(.invalidConfiguration)); return }
        requestsUsed += 1
        adapter.send(key: key, model: model, spec: spec) { [weak self] result in
            guard let self = self, token == self.generation else { return }
            completion(result)
        }
    }

    private func commit(id: String, transaction: String, reply: String, mode: String, token: Int) {
        guard token == generation else { return }
        committing = true
        coreRequest("commit_turn", params: ["transaction_id": transaction, "reply": reply, "mode": mode]) { [weak self] envelope in
            guard let self = self, token == self.generation else { return }
            self.committing = false
            guard envelope["ok"] as? Bool == true else {
                self.failTurn(id: id, message: envelope["error"] as? String ?? "The domain rejected the reply. No turn was committed.", token: token)
                return
            }
            self.busy = false; self.activeUIID = nil; self.pendingTransaction = nil
            self.pendingCaseProposal = nil
            self.forward(envelope, id: id)
        }
    }

    private func failTurn(id: String, message: String, token: Int) {
        guard token == generation else { return }
        adapter.cancel()
        if pendingTransaction != nil {
            pendingTransaction = nil
            coreRequest("cancel_turn") { [weak self] _ in
                guard let self = self, token == self.generation else { return }
                self.busy = false; self.activeUIID = nil; self.emit(id: id, ok: false, error: message)
            }
        } else { busy = false; activeUIID = nil; emit(id: id, ok: false, error: message) }
    }

    private func cancelCurrent(disconnect: Bool) -> String? {
        if disconnect { credential = nil; verified = false }
        // Once Core receives commit, its atomic save is the transaction's commit point.
        // A later cancel must not claim the already-saving turn was rolled back.
        if committing { return disconnect ? nil : "This turn is already being saved and cannot be cancelled." }
        generation += 1; adapter.cancel()
        if let id = activeUIID { emit(id: id, ok: false, error: "Turn cancelled. A request already sent may still be billed by the provider.") }
        let wasTurn = activeUIID != nil
        activeUIID = nil
        if pendingTransaction != nil {
            pendingTransaction = nil
            coreRequest("cancel_turn") { [weak self] _ in self?.busy = false; self?.emit(id: nil) }
        } else if !corePending && wasTurn { busy = false }
        return nil
    }

    private func saveExport(id: String, result: [String: Any]) {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = "witness-loop-export.json"
        panel.allowedContentTypes = [.json]
        activationSheet = true
        panel.beginSheetModal(for: window) { [weak self] response in
            guard let self = self else { return }
            self.activationSheet = false
            guard response == .OK, let url = panel.url else { self.emit(id: id, result: ["export_cancelled": true]); return }
            do {
                let data = try JSONSerialization.data(withJSONObject: result["export"] ?? result, options: [.prettyPrinted, .sortedKeys])
                try data.write(to: url, options: [.withoutOverwriting])
                self.emit(id: id, result: ["export_saved": true])
            } catch { self.emit(id: id, ok: false, error: "The export could not be written. Choose a new file name and try again.") }
        }
    }
}

if CommandLine.arguments.contains("--self-test") {
    exit(runNativeSelfTests())
}
let application = NSApplication.shared
let controller = AppController()
application.setActivationPolicy(.regular)
application.delegate = controller
application.run()
