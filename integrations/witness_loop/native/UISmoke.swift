import AppKit
import WebKit

// Opt-in offline bridge/DOM integration check. This does not replace human UAT.
final class OfflineUISmoke {
    private let webView: WKWebView
    private let screenshotURL: URL
    private let finish: (Int32) -> Void
    private var finished = false
    private var next = 0
    private var passed = 0
    private var lastRevision = -1
    private let steps: [(String, [String: Any])] = [
        ("start", ["player": "<b>HAL测试</b>", "style": "empathetic"]),
        ("turn", ["text": "我保证会保护你。"]),
        ("turn", ["text": "00:17 的那通电话是谁打来的？"]),
        ("advance", [:]),
        ("link", ["clues": ["clock", "call"]]),
        ("advance", [:]),
        ("verdict", [:]),
        ("developer", [:])
    ]
    init(webView: WKWebView, screenshotURL: URL, finish: @escaping (Int32) -> Void) { self.webView = webView; self.screenshotURL = screenshotURL; self.finish = finish }
    func run() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 45) { [weak self] in self?.end(false, "UI integration check timed out") }
        step()
    }
    private func step() {
        guard !finished else { return }
        guard next < steps.count else { checkDOM(); return }
        let (action, params) = steps[next]
        let identifier = "native-ui-test-\(next)"
        let script = """
        return await new Promise((resolve, reject) => {
          const previous = window.halReceive;
          const timer = setTimeout(() => { window.halReceive = previous; reject(new Error('timeout')); }, 6000);
          window.halReceive = function(envelope) {
            if (previous) previous(envelope);
            if (envelope.id === requestID) { clearTimeout(timer); window.halReceive = previous; resolve(envelope); }
          };
          window.webkit.messageHandlers.hal.postMessage({id:requestID, action:actionName, params:parameters});
        });
        """
        webView.callAsyncJavaScript(script, arguments: ["requestID": identifier, "actionName": action, "parameters": params], in: nil, in: .page) { [weak self] response in
            guard let self = self, !self.finished else { return }
            guard case .success(let value) = response, let envelope = value as? [String: Any], envelope["ok"] as? Bool == true,
                  let result = envelope["result"] as? [String: Any],
                  let activation = result["activation"] as? [String: Any], activation["state"] as? String == "OFFLINE",
                  activation["requests_used"] as? Int == 0 else { self.end(false, "Offline bridge action failed: \(action)"); return }
            if action != "developer" {
                guard let state = result["state"] as? [String: Any], let revision = state["revision"] as? Int, revision > self.lastRevision else { self.end(false, "State revision did not advance: \(action)"); return }
                self.lastRevision = revision
                if action == "verdict" && state["ending"] as? String != "truth" { self.end(false, "Expected truth ending from offline clues"); return }
            } else {
                guard result["developer"] is [String: Any] else { self.end(false, "Developer pathway assets unavailable"); return }
            }
            self.passed += 1
            print("PASS offline JS/native/Core action: \(action)")
            self.next += 1
            self.step()
        }
    }
    private func checkDOM() {
        let script = """
        document.querySelectorAll('dialog[open]').forEach(d => d.close());
        return {
          title: document.title,
          remaining: document.getElementById('remaining').textContent,
          dialogue: document.getElementById('dialogue').textContent,
          unsafeElements: document.getElementById('dialogue').querySelectorAll('.bubble > b b').length,
          literalPlayer: Array.from(document.querySelectorAll('#dialogue .bubble > b')).some(n => n.textContent === '<b>HAL测试</b>'),
          ending: document.getElementById('ending').hidden,
          endingTitle: document.getElementById('endingTitle').textContent,
          cards: document.getElementById('cards').children.length,
          keyFields: document.querySelectorAll('input[type=password]').length,
          csp: document.querySelector('meta[http-equiv="Content-Security-Policy"]').content
        };
        """
        webView.callAsyncJavaScript(script, arguments: [:], in: nil, in: .page) { [weak self] response in
            guard let self = self, !self.finished else { return }
            guard case .success(let value) = response, let dom = value as? [String: Any],
                  (dom["title"] as? String)?.contains("Witness Loop") == true,
                  (dom["dialogue"] as? String)?.isEmpty == false,
                  dom["unsafeElements"] as? Int == 0,
                  dom["literalPlayer"] as? Bool == true,
                  dom["ending"] as? Bool == false,
                  (dom["endingTitle"] as? String)?.isEmpty == false,
                  (dom["cards"] as? Int ?? 0) >= 3,
                  dom["keyFields"] as? Int == 0,
                  (dom["csp"] as? String)?.contains("connect-src 'none'") == true else { self.end(false, "DOM, CSP or renderer credential-boundary check failed"); return }
            self.passed += 1
            print("PASS offline specialist UI / text rendering / CSP / no renderer credential field")
            self.captureScreenshot()
        }
    }
    private func captureScreenshot() {
        webView.takeSnapshot(with: nil) { [weak self] image, error in
            guard let self = self, !self.finished else { return }
            guard error == nil, let image = image, let tiff = image.tiffRepresentation,
                  let bitmap = NSBitmapImageRep(data: tiff), let png = bitmap.representation(using: .png, properties: [:]) else { self.end(false, "UI screenshot could not be captured"); return }
            do {
                try png.write(to: self.screenshotURL, options: [.atomic])
                print("Offline UI screenshot: \(self.screenshotURL.path)")
                self.end(true, "\(self.passed) checks passed; no provider requests or real credentials. Isolated test data retained in .build-cache.")
            } catch { self.end(false, "UI screenshot could not be saved") }
        }
    }
    private func end(_ success: Bool, _ message: String) {
        guard !finished else { return }
        finished = true
        print("Native UI smoke: \(success ? "PASS" : "FAIL") — \(message)")
        finish(success ? 0 : 1)
    }
}
