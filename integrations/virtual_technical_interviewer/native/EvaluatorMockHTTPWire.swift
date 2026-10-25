// E4D-02C1B1A: DEVELOPMENT-ONLY loopback HTTP wire probe.
// Standalone Swift CLI, not linked into the production TIA App.
// No credentials, no OpenAI endpoint, no files, no grade authority.
import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

private let requestSchema = "tia-e4d02c1b1a-mock-wire-request/v1"
private let responseSchema = "tia-e4d02c1b1a-mock-wire-response/v1"
private let hex64 = try! NSRegularExpression(pattern: "^[a-f0-9]{64}$")
private let ident = try! NSRegularExpression(pattern: "^[a-z0-9_]{1,80}$")

private func matching(_ text: String, _ pattern: NSRegularExpression) -> Bool {
    return pattern.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)) != nil
}
private func fail(_ code: String) -> Never {
    let payload = ["ok": false, "code": code] as [String : Any]
    if let data = try? JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys]),
       let line = String(data: data, encoding: .utf8) { print(line) }
    exit(2)
}
private func parseJSON(_ data: Data) -> [String: Any]? {
    guard let parsed = try? JSONSerialization.jsonObject(with: data),
          let dict = parsed as? [String: Any] else { return nil }
    return dict
}
private final class RedirectRejector: NSObject, URLSessionTaskDelegate {
    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest,
                    completionHandler: @escaping (URLRequest?) -> Void) {
        completionHandler(nil)
    }
}

private final class CompletionBox: @unchecked Sendable {
    private let lock = NSLock()
    private var payload: Data? = nil
    private var code: Int? = nil
    private var failed = true
    func set(data: Data?, code: Int?, failed: Bool) {
        lock.lock(); defer { lock.unlock() }
        payload = data; self.code = code; self.failed = failed
    }
    func read() -> (data: Data?, code: Int?, failed: Bool) {
        lock.lock(); defer { lock.unlock() }
        return (payload, code, failed)
    }
}

private func run() {
    guard CommandLine.arguments.count == 3, CommandLine.arguments[1] == "--mock-port",
          let port = UInt16(CommandLine.arguments[2]), port > 0 else { fail("INVALID_MOCK_PORT") }
    let line = FileHandle.standardInput.readDataToEndOfFile()
    guard line.count > 0 && line.count <= 8192,
          let request = parseJSON(line),
          Set(request.keys) == Set(["schema","role","transport","transaction_id",
                                     "request_id","generation","source_sha256"]),
          request["schema"] as? String == requestSchema,
          request["role"] as? String == "evaluator",
          request["transport"] as? String == "LOCAL_LOOPBACK_MOCK_HTTP",
          let tx = request["transaction_id"] as? String, matching(tx, ident),
          let id = request["request_id"] as? String, matching(id, ident),
          let generation = request["generation"] as? String, matching(generation, ident),
          let digest = request["source_sha256"] as? String, matching(digest, hex64)
    else { fail("INVALID_MOCK_WIRE_REQUEST") }
    guard let address = URL(string: "http://127.0.0.1:\(port)/tia/evaluator/mock") else { fail("INVALID_LOOPBACK_URL") }
    var outbound = URLRequest(url: address)
    outbound.httpMethod = "POST"
    outbound.setValue("application/json", forHTTPHeaderField: "Content-Type")
    outbound.httpBody = try? JSONSerialization.data(withJSONObject: request, options: [.sortedKeys])
    outbound.timeoutInterval = 7
    let config = URLSessionConfiguration.ephemeral
    config.timeoutIntervalForRequest = 7
    config.timeoutIntervalForResource = 9
    let rejector = RedirectRejector()
    let session = URLSession(configuration: config, delegate: rejector, delegateQueue: nil)
    let semaphore = DispatchSemaphore(value: 0)
    let box = CompletionBox()
    let task = session.dataTask(with: outbound) { data, response, error in
        box.set(data: data, code: (response as? HTTPURLResponse)?.statusCode, failed: error != nil)
        semaphore.signal()
    }
    task.resume()
    if semaphore.wait(timeout: .now() + 10) != .success { task.cancel(); fail("MOCK_TIMEOUT") }
    session.invalidateAndCancel()
    let captured = box.read()
    guard !captured.failed, captured.code == 200,
          let bytes = captured.data, bytes.count > 0 && bytes.count <= 65536,
          let reply = parseJSON(bytes),
          Set(reply.keys) == Set(["schema","role","transport","transaction_id",
                                   "request_id","generation","source_sha256","proposal_json"]),
          reply["schema"] as? String == responseSchema,
          reply["role"] as? String == "evaluator",
          reply["transport"] as? String == "LOCAL_LOOPBACK_MOCK_HTTP",
          reply["transaction_id"] as? String == tx,
          reply["request_id"] as? String == id,
          reply["generation"] as? String == generation,
          reply["source_sha256"] as? String == digest,
          let proposal = reply["proposal_json"] as? String,
          !proposal.isEmpty, proposal.utf8.count <= 32768
    else { fail("MOCK_HTTP_RESPONSE_REJECTED") }
    // This response is NOT a validated grade. The trusted Python Host validates
    // strict JSON, citations, current source and transaction before review.
    if let encoded = try? JSONSerialization.data(withJSONObject: reply, options: [.sortedKeys]),
       let output = String(data: encoded, encoding: .utf8) {
        print(output)
    } else { fail("MOCK_SERIALIZATION_FAILED") }
}
run()
