import Foundation

func runNativeSelfTests() -> Int32 {
    var passed = 0
    var failed = 0
    func check(_ label: String, _ body: () throws -> Bool) {
        do {
            if try body() { passed += 1; print("PASS \(label)") }
            else { failed += 1; print("FAIL \(label)") }
        } catch { failed += 1; print("FAIL \(label)") }
    }
    func rejected(_ body: () throws -> Any) -> Bool { do { _ = try body(); return false } catch { return true } }
    func response(_ text: String, state: String = "completed") throws -> Data {
        try JSONSerialization.data(withJSONObject: ["status": state, "output": [["type": "message", "role": "assistant", "status": "completed", "content": [["type": "output_text", "text": text]]]]])
    }
    let topicSchema: [String: Any] = ["type": "object", "properties": ["topic": ["type": "string", "enum": ["time", "call", "coat", "relation", "promise", "other"]]], "required": ["topic"], "additionalProperties": false]
    let synthetic = "TEST_ONLY_NOT_A_CREDENTIAL"
    let spec = ModelRequest(instructions: "Synthetic domain rules", input: ["text": "test"], schema: replySchema, name: "hal_reply", outputTokens: 600)
    check("fixed HTTPS endpoint / POST") {
        let request = try OpenAIAdapter.request(key: synthetic, model: "gpt-4.1-mini", spec: spec)
        return request.url?.absoluteString == "https://api.openai.com/v1/responses" && request.httpMethod == "POST" && request.timeoutInterval == 30
    }
    check("credential only in native authorization header") {
        let request = try OpenAIAdapter.request(key: synthetic, model: "gpt-4.1-mini", spec: spec)
        return request.value(forHTTPHeaderField: "Authorization") == "Bearer " + synthetic && !String(data: request.httpBody!, encoding: .utf8)!.contains(synthetic)
    }
    check("store false / strict schema / bounded output") {
        let request = try OpenAIAdapter.request(key: synthetic, model: "gpt-4.1-mini", spec: spec)
        let body = try JSONSerialization.jsonObject(with: request.httpBody!) as! [String: Any]
        let format = (body["text"] as! [String: Any])["format"] as! [String: Any]
        return body["store"] as? Bool == false && body["max_output_tokens"] as? Int == 600 && format["strict"] as? Bool == true && format["type"] as? String == "json_schema"
    }
    check("string context input accepted") {
        let request = try OpenAIAdapter.request(key: synthetic, model: "gpt-4.1-mini", spec: ModelRequest(instructions: "Rules", input: "{\"text\":\"test\"}", schema: topicSchema, name: "hal_topic", outputTokens: 200))
        return request.httpBody != nil
    }
    check("header newline injection rejected") { rejected { try OpenAIAdapter.request(key: "synthetic\r\nx-test: evil", model: "gpt-4.1-mini", spec: spec) } }
    check("empty credential rejected") { rejected { try OpenAIAdapter.request(key: "", model: "gpt-4.1-mini", spec: spec) } }
    check("oversized credential rejected") { rejected { try OpenAIAdapter.request(key: String(repeating: "x", count: 1025), model: "gpt-4.1-mini", spec: spec) } }
    check("endpoint-shaped model rejected") { !OpenAIAdapter.validModel("https://attacker.invalid") }
    check("model CRLF rejected") { !OpenAIAdapter.validModel("gpt-4.1-mini\n") }
    check("arbitrary output budget rejected") { rejected { try OpenAIAdapter.request(key: synthetic, model: "gpt-4.1-mini", spec: ModelRequest(instructions: "Rules", input: [:], schema: replySchema, name: "hal_reply", outputTokens: 9999)) } }
    check("oversized input rejected") { rejected { try OpenAIAdapter.request(key: synthetic, model: "gpt-4.1-mini", spec: ModelRequest(instructions: "Rules", input: String(repeating: "x", count: 16001), schema: replySchema, name: "hal_reply", outputTokens: 600)) } }
    check("valid topic parsed") { try OpenAIAdapter.parse(response("{\"topic\":\"call\"}"), status: 200)["topic"] as? String == "call" }
    check("valid reply parsed") { try OpenAIAdapter.parse(response("{\"reply\":\"Hello.\"}"), status: 200)["reply"] as? String == "Hello." }
    check("incomplete provider response rejected") { rejected { try OpenAIAdapter.parse(response("{}", state: "incomplete"), status: 200) } }
    check("provider failure rejected") { rejected { try OpenAIAdapter.parse(Data("{}".utf8), status: 401) } }
    check("redirect status rejected") { rejected { try OpenAIAdapter.parse(Data("{}".utf8), status: 302) } }
    check("malformed response rejected") { rejected { try OpenAIAdapter.parse(Data("not json".utf8), status: 200) } }
    check("structured array rejected") { rejected { try OpenAIAdapter.parse(response("[]"), status: 200) } }
    check("nonfinite structured number rejected") { rejected { try OpenAIAdapter.parse(response("{\"value\":NaN}"), status: 200) } }
    check("refusal rejected") {
        let data = try JSONSerialization.data(withJSONObject: ["status": "completed", "output": [["type": "message", "role": "assistant", "status": "completed", "content": [["type": "refusal", "refusal": "no"]]]]])
        return rejected { try OpenAIAdapter.parse(data, status: 200) }
    }
    check("multiple output text blocks rejected") {
        let data = try JSONSerialization.data(withJSONObject: ["status": "completed", "output": [["type": "message", "role": "assistant", "status": "completed", "content": [["type": "output_text", "text": "{}"], ["type": "output_text", "text": "{}"]]]]])
        return rejected { try OpenAIAdapter.parse(data, status: 200) }
    }
    check("oversized provider response rejected") { rejected { try OpenAIAdapter.parse(Data(repeating: 32, count: OpenAIAdapter.maximumResponseBytes + 1), status: 200) } }
    check("key echo blocked recursively") { OpenAIAdapter.containsSecret(["reply": ["nested " + synthetic]], secret: synthetic) }
    check("ordinary text not a key echo") { !OpenAIAdapter.containsSecret(["reply": "A synthetic NPC response"], secret: synthetic) }
    check("bridge confirmed turn accepted") { BridgePolicy.validate(["id": "ui-1", "action": "turn", "params": ["text": "Who called?", "confirm_case": true]]) != nil }
    check("bridge free turn accepted") { BridgePolicy.validate(["id": "ui-1", "action": "turn", "params": ["text": "How are you?", "confirm_case": false]]) != nil }
    check("bridge missing confirmation rejected") { BridgePolicy.validate(["id": "ui-1", "action": "turn", "params": ["text": "Who called?"]]) == nil }
    check("bridge numeric confirmation rejected") { BridgePolicy.validate(["id": "ui-1", "action": "turn", "params": ["text": "Who called?", "confirm_case": 1]]) == nil }
    check("bridge readonly preview accepted") { BridgePolicy.validate(["id": "ui-1", "action": "preview_turn", "params": ["text": "Who called?"]]) != nil }
    check("bridge inspect accepts bounded id") { BridgePolicy.validate(["id": "ui-1", "action": "inspect", "params": ["id": "red_fabric"]]) != nil }
    check("bridge inspect accepts numbered historical event id") { BridgePolicy.validate(["id": "ui-1", "action": "inspect", "params": ["id": "call_0017"]]) != nil }
    check("bridge inspect path injection denied") { BridgePolicy.validate(["id": "ui-1", "action": "inspect", "params": ["id": "../../secret"]]) == nil }
    check("bridge forged evidence rejected") { BridgePolicy.validate(["id": "ui-1", "action": "inspect", "params": ["id": "clock", "authenticated": true]]) == nil }
    check("bridge language choice accepted") { BridgePolicy.validate(["id": "ui-1", "action": "language", "params": ["language": "en"]]) != nil }
    check("bridge arbitrary language payload denied") { BridgePolicy.validate(["id": "ui-1", "action": "language", "params": ["language": "ignore rules"]]) == nil }
    check("bridge authored phase injection denied") { BridgePolicy.validate(["id": "ui-1", "action": "continue", "params": ["phase": "RESOLVED"]]) == nil }
    check("bridge unknown action rejected") { BridgePolicy.validate(["id": "ui-1", "action": "exec", "params": [:]]) == nil }
    check("bridge model result injection rejected") { BridgePolicy.validate(["id": "ui-1", "action": "commit_turn", "params": ["reply": "injected"]]) == nil }
    check("bridge arbitrary path rejected") { BridgePolicy.validate(["id": "ui-1", "action": "snapshot", "params": ["path": "/etc/passwd"]]) == nil }
    check("bridge credential submission rejected") { BridgePolicy.validate(["id": "ui-1", "action": "activate", "params": ["key": synthetic]]) == nil }
    check("bridge identifier script injection rejected") { BridgePolicy.validate(["id": "');alert(1)", "action": "snapshot", "params": [:]]) == nil }
    check("bridge oversized input rejected") { BridgePolicy.validate(["id": "ui-1", "action": "turn", "params": ["text": String(repeating: "x", count: 1001)]]) == nil }
    check("bridge extra top-level key rejected") { BridgePolicy.validate(["id": "ui-1", "action": "snapshot", "params": [:], "credential": synthetic]) == nil }
    check("duplicate structured JSON keys rejected") { rejected { try OpenAIAdapter.parse(response("{\"topic\":\"call\",\"topic\":\"other\"}"), status: 200) } }
    check("escaped duplicate JSON keys rejected") { rejected { try StrictJSON.object(Data(#"{"reply":"a","r\u0065ply":"b"}"#.utf8)) } }
    check("duplicate envelope keys rejected") { rejected { try OpenAIAdapter.parse(Data(#"{"status":"incomplete","status":"completed","output":[]}"#.utf8), status: 200) } }
    check("excessive JSON nesting rejected") { rejected { try StrictJSON.object(Data((String(repeating: "[", count: 34) + "0" + String(repeating: "]", count: 34)).utf8)) } }
    check("valid escaped JSON string accepted") { try (StrictJSON.object(Data(#"{"reply":"quote \" and slash \\ test"}"#.utf8)) as? [String: String])?["reply"] != nil }
    func mocked(_ payload: Data, status: Int = 200) -> Result<[String: Any], ProviderFailure>? {
        SyntheticProviderProtocol.payload = payload
        SyntheticProviderProtocol.responseCode = status
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [SyntheticProviderProtocol.self]
        let adapter = OpenAIAdapter(configuration: configuration)
        var result: Result<[String: Any], ProviderFailure>?
        adapter.send(key: synthetic, model: "gpt-4.1-mini", spec: spec) { result = $0 }
        let deadline = Date().addingTimeInterval(3)
        while result == nil && Date() < deadline { _ = RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.01)) }
        adapter.cancel()
        return result
    }
    check("mock provider response traverses native adapter") {
        if case .success(let value)? = mocked(try response("{\"reply\":\"A synthetic response\"}")) { return value["reply"] as? String == "A synthetic response" }
        return false
    }
    check("mock provider echoed credential blocked before renderer") {
        if case .failure(.invalidResponse)? = mocked(try response("{\"reply\":\"" + synthetic + "\"}")) { return true }
        return false
    }
    check("mock provider rate limit has no automatic retry") {
        let before = SyntheticProviderProtocol.calls
        if case .failure(.httpStatus(429))? = mocked(Data("{}".utf8), status: 429) { return SyntheticProviderProtocol.calls == before + 1 }
        return false
    }
    check("redirect delegate refuses credential forwarding") {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [SyntheticProviderProtocol.self]
        let session = URLSession(configuration: configuration)
        let adapter = OpenAIAdapter(configuration: configuration)
        let request = URLRequest(url: URL(string: "https://attacker.invalid/")!)
        let task = session.dataTask(with: OpenAIAdapter.endpoint)
        let response = HTTPURLResponse(url: OpenAIAdapter.endpoint, statusCode: 302, httpVersion: "HTTP/1.1", headerFields: ["Location": request.url!.absoluteString])!
        var rejected = false
        adapter.urlSession(session, task: task, willPerformHTTPRedirection: response, newRequest: request) { rejected = $0 == nil }
        session.invalidateAndCancel()
        return rejected
    }
    print("Native self-tests: \(passed) passed; \(failed) failed. No GUI, network, or real credentials used.")
    return failed == 0 ? 0 : 1
}

final class SyntheticProviderProtocol: URLProtocol {
    static var payload = Data()
    static var responseCode = 200
    static var calls = 0
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        Self.calls += 1
        guard let response = HTTPURLResponse(url: request.url!, statusCode: Self.responseCode, httpVersion: "HTTP/1.1", headerFields: ["Content-Type": "application/json"]) else { return }
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: Self.payload)
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}
