import AppKit
import WebKit
import UniformTypeIdentifiers

final class TIAApp: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate, WKUIDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var worker: TIAWorker?
    private var indexURL: URL!
    let portal = NativePortal()
    private var busy = false
    private var seenIDs = Set<String>()
    private var lastState: [String: Any] = [:]
    private var portalSheet: NSAlert?
    private var smoke: TIAUISmoke?
    let uiTesting = CommandLine.arguments.contains("--ui-self-test") || CommandLine.arguments.contains("--ui-recovery-test") || CommandLine.arguments.contains("--ui-setup-test")
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
                self?.portal.disconnect()
                self?.emit(["ok": false, "error": "LOCAL_CONTROLLER_UNAVAILABLE"])
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
        guard !busy, portalSheet == nil else { emit(["id": id, "ok": false, "error": "NATIVE_BUSY"]); return }
        if action.hasPrefix("setup_"), action != "setup_back", portal.state != "activated-unverified" {
            emit(["id": id, "ok": false, "state": lastState, "error": "NATIVE_CREDENTIAL_CONFIGURATION_REQUIRED"]); return
        }
        if action == "api_portal" {
            guard lastState["screen"] as? String == "API_PORTAL" else { emit(["id": id, "ok": false, "error": "INVALID_TRANSITION"]); return }
            openPortal { self.respondWithState(id) }; return
        }
        if action == "disconnect" { portal.disconnect(); respondWithState(id); return }
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

    private func respondWithState(_ id: String) { emit(["id": id, "ok": true, "state": lastState]) }
    func emit(_ raw: [String: Any]) {
        var result = raw
        if var state = result["state"] as? [String: Any] {
            state["activation"] = portal.publicState
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
        Live calls are disabled in this increment. A stored key is UNVERIFIED, not authenticated.
        本版本不调用 API；保存密钥不代表验证或成功激活。密钥仅留在此原生进程内，断开或退出即清除。
        """
        alert.addButton(withTitle: "Keep locally · 未验证")
        alert.addButton(withTitle: "Cancel / 取消")
        let container = NSView(frame: NSRect(x: 0, y: 0, width: 440, height: 94))
        let field = NSSecureTextField(frame: NSRect(x: 0, y: 58, width: 440, height: 26))
        field.placeholderString = "API key (session only)"; field.setAccessibilityLabel("Session-only API key")
        let consent = NSButton(checkboxWithTitle: "Keep this key in memory only / 仅在本次运行中保留", target: nil, action: nil)
        consent.frame = NSRect(x: 0, y: 23, width: 440, height: 24)
        container.addSubview(field); container.addSubview(consent); alert.accessoryView = container
        alert.buttons[0].isEnabled = false
        let delegate = CredentialFieldDelegate { [weak alert, weak field, weak consent] in
            alert?.buttons[0].isEnabled = NativePortal.validCredential(field?.stringValue ?? "") && consent?.state == .on
        }
        field.delegate = delegate
        consent.target = delegate; consent.action = #selector(CredentialFieldDelegate.changed)
        portalSheet = alert
        alert.beginSheetModal(for: window) { [weak self] result in
            guard let self = self else { return }
            _ = delegate // Retain for the sheet's entire lifetime.
            if result == .alertFirstButtonReturn {
                _ = self.portal.configure(field.stringValue, consent: consent.state == .on)
            }
            field.stringValue = ""; consent.state = .off
            self.portalSheet = nil; completion()
        }
        alert.window.makeFirstResponder(field)
    }

    // UI test checks the real native sheet; it never enters a credential.
    var portalIsVisible: Bool { portalSheet?.messageText == "API Portal · OpenAI" }
    func cancelPortalForTest() {
        guard uiTesting, let alert = portalSheet else { return }
        window.endSheet(alert.window, returnCode: .alertSecondButtonReturn)
    }
    func enterSyntheticCredentialForTest() -> Bool {
        guard uiTesting, let alert = portalSheet, portalIsVisible,
              let field = alert.accessoryView?.subviews.compactMap({ $0 as? NSSecureTextField }).first,
              let consent = alert.accessoryView?.subviews.compactMap({ $0 as? NSButton }).first,
              let delegate = field.delegate as? CredentialFieldDelegate else { return false }
        field.stringValue = "synthetic-ui-fixture-not-a-real-key"
        consent.state = .on; delegate.changed()
        guard alert.buttons[0].isEnabled else { return false }
        window.endSheet(alert.window, returnCode: .alertFirstButtonReturn)
        return true
    }
    private func exportReceipt(_ result: [String: Any], completion: @escaping (String) -> Void) {
        guard let exported = result["export"] ?? result["record"],
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
    exit(runNativeTests())
}
let application = NSApplication.shared
application.setActivationPolicy(.regular)
let delegate = TIAApp()
application.delegate = delegate
application.run()
