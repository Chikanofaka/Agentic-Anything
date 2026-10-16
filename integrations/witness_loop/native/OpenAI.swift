import Foundation

// Native-only fixed-endpoint provider adapter. Credentials never cross the WebKit bridge.
enum ProviderFailure: Error {
    case invalidConfiguration, invalidRequest, transport, httpStatus(Int), invalidResponse, refused, incomplete, oversized
    var publicMessage: String {
        switch self {
        case .invalidConfiguration: return "The provider model or credential format is invalid."
        case .invalidRequest: return "The domain did not produce a valid bounded model request."
        case .transport: return "The provider request failed or timed out. No turn was committed."
        case .httpStatus(let code): return "OpenAI returned HTTP \(code). No turn was committed."
        case .invalidResponse: return "OpenAI returned an invalid structured response. No turn was committed."
        case .refused: return "The provider declined this request. No turn was committed."
        case .incomplete: return "The provider response was incomplete. No turn was committed."
        case .oversized: return "The provider response exceeded the local size limit."
        }
    }
}

struct ModelRequest {
    let instructions: String
    let input: Any
    let schema: [String: Any]
    let name: String
    let outputTokens: Int
}

final class OpenAIAdapter: NSObject, URLSessionTaskDelegate, URLSessionDataDelegate {
    static let endpoint = URL(string: "https://api.openai.com/v1/responses")!
    static let maximumResponseBytes = 256 * 1024
    private let configuration: URLSessionConfiguration
    private var session: URLSession?
    private var task: URLSessionDataTask?
    private var completion: ((Result<[String: Any], ProviderFailure>) -> Void)?
    private var received = Data()
    private var status = 0
    private var activeKey: String?
    private let lock = NSLock()

    init(configuration: URLSessionConfiguration = .ephemeral) {
        self.configuration = configuration
        super.init()
    }

    static func validModel(_ model: String) -> Bool {
        !model.isEmpty && model.count <= 80 && model.range(of: "\\A[A-Za-z0-9][A-Za-z0-9._-]*\\z", options: .regularExpression) != nil
    }

    static func request(key: String, model: String, spec: ModelRequest) throws -> URLRequest {
        guard validModel(model), !key.isEmpty, key.utf8.count <= 1024,
              key.unicodeScalars.allSatisfy({ $0.value >= 33 && $0.value <= 126 }) else { throw ProviderFailure.invalidConfiguration }
        guard !spec.instructions.isEmpty, spec.instructions.utf8.count <= 32768,
              [200, 600].contains(spec.outputTokens), ["hal_topic", "hal_reply"].contains(spec.name),
              (spec.input is String || JSONSerialization.isValidJSONObject(spec.input)), JSONSerialization.isValidJSONObject(spec.schema) else { throw ProviderFailure.invalidRequest }
        let input: String
        if let text = spec.input as? String { input = text }
        else {
            let inputData = try JSONSerialization.data(withJSONObject: spec.input, options: [.sortedKeys])
            guard let text = String(data: inputData, encoding: .utf8) else { throw ProviderFailure.invalidRequest }
            input = text
        }
        guard input.utf8.count <= 16000 else { throw ProviderFailure.invalidRequest }
        let body: [String: Any] = [
            "model": model, "instructions": spec.instructions, "input": input,
            "max_output_tokens": spec.outputTokens, "store": false,
            "text": ["format": ["type": "json_schema", "name": spec.name, "strict": true, "schema": spec.schema]]
        ]
        var request = URLRequest(url: endpoint, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 30)
        request.httpMethod = "POST"
        request.setValue("Bearer " + key, forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        return request
    }

    static func parse(_ data: Data, status: Int) throws -> [String: Any] {
        guard data.count <= maximumResponseBytes else { throw ProviderFailure.oversized }
        guard status == 200 else { throw ProviderFailure.httpStatus(status) }
        guard let body = try StrictJSON.object(data) as? [String: Any],
              let state = body["status"] as? String else { throw ProviderFailure.invalidResponse }
        guard state == "completed" else { throw ProviderFailure.incomplete }
        guard let output = body["output"] as? [[String: Any]] else { throw ProviderFailure.invalidResponse }
        var texts = [String]()
        for item in output {
            if item["type"] as? String == "refusal" { throw ProviderFailure.refused }
            guard item["type"] as? String == "message" else { continue }
            guard item["role"] as? String == "assistant", item["status"] as? String == "completed",
                  let content = item["content"] as? [[String: Any]] else { throw ProviderFailure.invalidResponse }
            for part in content {
                if part["type"] as? String == "refusal" { throw ProviderFailure.refused }
                guard part["type"] as? String == "output_text", let text = part["text"] as? String else { throw ProviderFailure.invalidResponse }
                texts.append(text)
            }
        }
        guard texts.count == 1, let text = texts.first, text.utf8.count <= 16384,
              let encoded = text.data(using: .utf8), let object = try StrictJSON.object(encoded) as? [String: Any] else { throw ProviderFailure.invalidResponse }
        // The caller checks the exact domain-specific output keys before passing values to Core.
        return object
    }

    func send(key: String, model: String, spec: ModelRequest, completion: @escaping (Result<[String: Any], ProviderFailure>) -> Void) {
        let request: URLRequest
        do { request = try Self.request(key: key, model: model, spec: spec) }
        catch { completion(.failure((error as? ProviderFailure) ?? .invalidRequest)); return }
        lock.lock()
        guard self.completion == nil else { lock.unlock(); completion(.failure(.invalidRequest)); return }
        self.completion = completion
        activeKey = key
        received = Data(); status = 0
        configuration.urlCache = nil
        configuration.httpCookieStorage = nil
        configuration.urlCredentialStorage = nil
        configuration.httpShouldSetCookies = false
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 30
        configuration.requestCachePolicy = .reloadIgnoringLocalCacheData
        session = URLSession(configuration: configuration, delegate: self, delegateQueue: nil)
        task = session!.dataTask(with: request)
        let active = task
        lock.unlock()
        active?.resume()
    }

    func cancel() {
        lock.lock()
        let current = task
        let currentSession = session
        completion = nil; task = nil; session = nil; activeKey = nil; received = Data()
        lock.unlock()
        current?.cancel(); currentSession?.invalidateAndCancel()
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        completionHandler(nil) // Never forward a credential to a redirect target.
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse, completionHandler: @escaping (URLSession.ResponseDisposition) -> Void) {
        guard response.url == Self.endpoint, let http = response as? HTTPURLResponse,
              response.expectedContentLength <= Int64(Self.maximumResponseBytes) else {
            completionHandler(.cancel); finish(.failure(.oversized), session: session); return
        }
        lock.lock(); status = http.statusCode; lock.unlock()
        completionHandler(.allow)
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        lock.lock()
        guard self.session === session else { lock.unlock(); return }
        let tooLarge = received.count + data.count > Self.maximumResponseBytes
        if !tooLarge { received.append(data) }
        lock.unlock()
        if tooLarge { dataTask.cancel(); finish(.failure(.oversized), session: session) }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        lock.lock(); let data = received; let code = status; let key = activeKey; let current = self.session === session; lock.unlock()
        guard current else { return }
        if error != nil { finish(.failure(.transport), session: session); return }
        do {
            let value = try Self.parse(data, status: code)
            guard let key = key, !Self.containsSecret(value, secret: key) else { throw ProviderFailure.invalidResponse }
            finish(.success(value), session: session)
        }
        catch { finish(.failure((error as? ProviderFailure) ?? .invalidResponse), session: session) }
    }

    static func containsSecret(_ value: Any, secret: String) -> Bool {
        if let text = value as? String { return text.contains(secret) }
        if let values = value as? [Any] { return values.contains { containsSecret($0, secret: secret) } }
        if let object = value as? [String: Any] { return object.contains { $0.key.contains(secret) || containsSecret($0.value, secret: secret) } }
        return false
    }

    private func finish(_ result: Result<[String: Any], ProviderFailure>, session: URLSession) {
        lock.lock()
        guard self.session === session else { lock.unlock(); return }
        let callback = completion
        completion = nil; task = nil; self.session = nil; activeKey = nil; received = Data()
        lock.unlock()
        session.finishTasksAndInvalidate()
        DispatchQueue.main.async { callback?(result) }
    }
}
