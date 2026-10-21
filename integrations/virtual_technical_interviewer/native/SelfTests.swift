import Foundation

func runNativeTests() -> Int32 {
    var failures = 0
    var checks = 0
    func check(_ label: String, _ condition: @autoclosure () -> Bool) {
        checks += 1
        if condition() { print("PASS \(label)") }
        else { failures += 1; print("FAIL \(label)") }
    }
    func request(_ action: String, _ params: [String: Any] = [:]) -> [String: Any] {
        ["id": "test-1", "action": action, "params": params]
    }
    let entry = URL(fileURLWithPath: "/fixture/ui/index.html")
    check("accessibility fragment retains bridge", BridgePolicy.allowedDocument(URL(string: entry.absoluteString + "#main"), entry: entry))
    check("query cannot change document origin", !BridgePolicy.allowedDocument(URL(string: entry.absoluteString + "?source=x"), entry: entry))
    check("external page rejected", !BridgePolicy.allowedDocument(URL(string: "https://example.invalid/index.html"), entry: entry))
    check("neighbor file rejected", !BridgePolicy.allowedDocument(URL(fileURLWithPath: "/fixture/ui/other.html"), entry: entry))
    for action in BridgePolicy.emptyActions {
        check("allow exact command \(action)", BridgePolicy.validate(request(action)) != nil)
        check("reject extra params \(action)", BridgePolicy.validate(request(action, ["key": "synthetic"])) == nil)
    }
    check("no arbitrary process execution", BridgePolicy.validate(request("exec", ["command": "true"])) == nil)
    check("no host phase mutation", BridgePolicy.validate(request("set_phase", ["phase": "COMPLETE"])) == nil)
    check("no renderer credentials", BridgePolicy.validate(request("api_portal", ["credential": "synthetic"])) == nil)
    check("bounded id", BridgePolicy.validate(["id": String(repeating: "a", count: 65), "action": "snapshot", "params": [:]]) == nil)
    check("exact envelope", BridgePolicy.validate(["id": "1", "action": "snapshot", "params": [:], "role": "host"]) == nil)
    check("language allowlist", BridgePolicy.validate(request("language", ["language": "zh"])) != nil)
    check("unknown language", BridgePolicy.validate(request("language", ["language": "xx"])) == nil)
    for kind in ["clarify", "plan", "implement", "test", "help"] {
        check("candidate \(kind)", BridgePolicy.validate(request("tutorial_submit", ["kind": kind, "text": "<script>literal</script>"])) != nil)
    }
    check("empty candidate rejected", BridgePolicy.validate(request("tutorial_submit", ["kind": "plan", "text": " "])) == nil)
    check("UTF8 byte bound", BridgePolicy.validate(request("tutorial_submit", ["kind": "plan", "text": String(repeating: "中", count: 2731)])) == nil)
    check("no score command", BridgePolicy.validate(request("tutorial_submit", ["kind": "score", "text": "100"])) == nil)
    let portal = NativePortal()
    check("offline initially", portal.state == "offline")
    check("empty key not activated", !portal.configure("", consent: true) && portal.state == "offline")
    check("no consent not activated", !portal.configure("synthetic-fixture-not-a-key", consent: false))
    check("newline credential rejected", !portal.configure("synthetic-key\nheader", consent: true))
    check("bounded credential", !portal.configure(String(repeating: "x", count: 1025), consent: true))
    check("local fixture explicitly unverified", portal.configure("synthetic-fixture-not-a-key", consent: true) && portal.state == "activated-unverified")
    let data = try! JSONSerialization.data(withJSONObject: portal.publicState)
    let text = String(data: data, encoding: .utf8)!
    check("credential never serialized", !text.contains("synthetic-fixture"))
    check("no authentication claim", portal.publicState["authenticated"] as? Bool == false)
    check("live calls disabled", portal.publicState["live_enabled"] as? Bool == false && portal.requestsUsed == 0)
    portal.disconnect()
    check("disconnect clears activation", portal.state == "offline" && portal.requestsUsed == 0)
    print("Native tests: \(checks - failures) passed, \(failures) failed; provider requests: 0")
    return failures == 0 ? 0 : 1
}
