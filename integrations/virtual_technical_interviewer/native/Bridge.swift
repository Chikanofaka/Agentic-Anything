import Foundation
import CoreFoundation

// Versioned renderer contract. Neither credentials nor arbitrary executable targets
// are accepted here. The Python host independently validates the same boundary.
enum BridgePolicy {
    static func allowedDocument(_ url: URL?, entry: URL) -> Bool {
        guard let url = url, url.isFileURL, url.query == nil else { return false }
        return url.standardizedFileURL.path == entry.standardizedFileURL.path
    }
    static let emptyActions: Set<String> = [
        "snapshot", "tutorial_start", "tutorial_next", "tutorial_back",
        "tutorial_complete", "tutorial_replay", "choose_real", "reset",
        "export", "api_portal", "disconnect"
    ]
    static func validate(_ value: Any) -> (String, String, [String: Any])? {
        guard let body = value as? [String: Any],
              Set(body.keys) == ["id", "action", "params"],
              let id = body["id"] as? String,
              id.range(of: "\\A[A-Za-z0-9_-]{1,64}\\z", options: .regularExpression) != nil,
              let action = body["action"] as? String,
              let params = body["params"] as? [String: Any],
              JSONSerialization.isValidJSONObject(body),
              let data = try? JSONSerialization.data(withJSONObject: body),
              data.count <= 16384 else { return nil }
        if emptyActions.contains(action) {
            guard params.isEmpty else { return nil }
        } else if action == "language" {
            guard Set(params.keys) == ["language"], let lang = params["language"] as? String,
                  ["en", "zh"].contains(lang) else { return nil }
        } else if action == "tutorial_submit" {
            guard Set(params.keys) == ["kind", "text"],
                  let kind = params["kind"] as? String,
                  ["clarify", "plan", "implement", "test", "help"].contains(kind),
                  let text = params["text"] as? String,
                  !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                  text.utf8.count <= 8192 else { return nil }
        } else { return nil }
        return (id, action, params)
    }
}

// Credentials only exist in this native object. No method serializes them. This
// increment deliberately has no network transport: configuration is NOT authentication.
final class NativePortal {
    private var credential: String?
    private(set) var state = "offline"
    private(set) var requestsUsed = 0
    static func validCredential(_ key: String) -> Bool {
        (16...1024).contains(key.utf8.count)
            && key.unicodeScalars.allSatisfy { (33...126).contains($0.value) }
    }
    @discardableResult func configure(_ key: String, consent: Bool) -> Bool {
        guard consent, Self.validCredential(key) else { return false }
        credential = key
        state = "activated-unverified"
        return true
    }
    func disconnect() { credential = nil; state = "offline" }
    var publicState: [String: Any] {
        ["state": state, "requests_used": requestsUsed, "live_enabled": false,
         "authenticated": false, "provider": "OpenAI", "reason": "LIVE_TRANSPORT_DISABLED"]
    }
}
