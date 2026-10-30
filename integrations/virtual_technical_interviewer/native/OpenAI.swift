import Foundation
import CoreFoundation
import CryptoKit

// TIA's native-only network boundary, adapted from Witness Loop's reviewed transport.
// Domain authority and prompt construction remain in the Python controller.
enum TIAProviderFailure: Error {
    case invalidConfiguration, invalidRequest, notActivated, consentRequired, budgetExceeded
    case invalidCredentials, modelUnavailable, usageLimit, rateLimited, permissionDenied
    case transport, timeout, cancelled, redirect, httpStatus(Int)
    case invalidResponse, refused, incomplete, oversized

    var code: String {
        switch self {
        case .invalidConfiguration: return "INVALID_PROVIDER_CONFIGURATION"
        case .invalidRequest: return "INVALID_PROVIDER_REQUEST"
        case .notActivated: return "PROVIDER_NOT_ACTIVATED"
        case .consentRequired: return "PAID_CONSENT_REQUIRED"
        case .budgetExceeded: return "REQUEST_LIMIT_REACHED"
        case .invalidCredentials: return "INVALID_CREDENTIALS"
        case .modelUnavailable: return "MODEL_UNAVAILABLE"
        case .usageLimit: return "PROVIDER_USAGE_LIMIT"
        case .rateLimited: return "PROVIDER_RATE_LIMIT"
        case .permissionDenied: return "PROVIDER_PERMISSION_DENIED"
        case .transport: return "PROVIDER_NETWORK_ERROR"
        case .timeout: return "PROVIDER_TIMEOUT"
        case .cancelled: return "PROVIDER_CANCELLED"
        case .redirect: return "PROVIDER_REDIRECT_REJECTED"
        case .httpStatus: return "PROVIDER_HTTP_ERROR"
        case .invalidResponse: return "INVALID_PROVIDER_RESPONSE"
        case .refused: return "PROVIDER_REFUSED"
        case .incomplete: return "INCOMPLETE_PROVIDER_RESPONSE"
        case .oversized: return "PROVIDER_RESPONSE_TOO_LARGE"
        }
    }
    var publicMessage: String {
        switch self {
        case .invalidConfiguration: return "Check the model, credential format and request limit in the native API Portal."
        case .invalidRequest: return "The controller did not authorize a valid bounded request."
        case .notActivated: return "Activate a provider in the native API Portal first."
        case .consentRequired: return "Explicit native paid-request consent is required."
        case .budgetExceeded: return "The session request limit has been reached."
        case .invalidCredentials: return "OpenAI rejected the credential. Reconnect in the native API Portal."
        case .modelUnavailable: return "The selected model is unavailable to this account."
        case .usageLimit: return "OpenAI reported an account usage or billing limit."
        case .rateLimited: return "OpenAI rate-limited this request. No automatic retry was made."
        case .permissionDenied: return "OpenAI denied this account permission for the request."
        case .transport: return "The provider could not be reached. No model reply was committed."
        case .timeout: return "The provider timed out. No model reply was committed."
        case .cancelled: return "The request was cancelled. An already sent request may still be billed."
        case .redirect: return "The provider redirect was rejected. Credentials were not forwarded."
        case .httpStatus(let status): return "OpenAI returned HTTP \(status). No model reply was committed."
        case .invalidResponse: return "OpenAI returned an invalid structured response. No model reply was committed."
        case .refused: return "The provider declined this request. No model reply was committed."
        case .incomplete: return "The provider response was incomplete. No model reply was committed."
        case .oversized: return "The provider response exceeded the local size limit."
        }
    }
}

// The Host supplies criterion-specific candidate aliases. Structured output
// constrains generation; both native and Host still validate the actual reply.
struct TIAEvaluatorReplyContract {
    static let version = "tia-evaluator-structured/v2"
    static let ids = ["T01", "T02", "T03", "T04", "T05", "C01", "C02", "C03", "C04", "C05", "C06"]
    let aliases: [String: [String]]
    let failedSQL: Bool

    init(context: [String: Any]) throws {
        guard context["response_contract"] as? String == Self.version,
              context["evidence_policy"] as? String == "tia-evaluator-evidence/v2",
              context["continuity_policy"] as? String == "tia-continuity/v3",
              let criteria = context["criteria"] as? [[String: Any]], criteria.count == Self.ids.count,
              let conversation = context["conversation"] as? [[String: Any]],
              let execution = context["local_execution"] as? [String: Any],
              let status = execution["status"] as? String else { throw TIAProviderFailure.invalidRequest }
        let candidates = conversation.filter { $0["actor"] as? String == "candidate" }
        let pool = candidates.compactMap { $0["alias"] as? String }
        guard pool.count == candidates.count, Set(pool).count == pool.count,
              pool.allSatisfy({ $0.range(of: "\\Ae[1-9][0-9]{0,5}\\z", options: .regularExpression) != nil })
        else { throw TIAProviderFailure.invalidRequest }
        var allowed = [String: [String]]()
        for (id, criterion) in zip(Self.ids, criteria) {
            guard criterion["id"] as? String == id,
                  let values = criterion["allowed_aliases"] as? [String],
                  Set(values).count == values.count, Set(values).isSubset(of: Set(pool)),
                  let canPropose = criterion["can_propose_anchor"] as? Bool, canPropose == !values.isEmpty
            else { throw TIAProviderFailure.invalidRequest }
            // C06 has no explicit closing-speech event in this version.
            guard id != "C06" || values.isEmpty,
                  id != "T01" || values.isEmpty || ["PASSED", "FAILED"].contains(status)
            else { throw TIAProviderFailure.invalidRequest }
            allowed[id] = values
        }
        // OpenAI's schema enum capacity is a request resource bound, never a
        // conversation-turn cap. Fail before a paid request, without truncation.
        guard allowed.values.reduce(0, { $0 + $1.count }) + 4 * Self.ids.count <= 1000
        else { throw TIAProviderFailure.invalidRequest }
        aliases = allowed; failedSQL = status == "FAILED"
    }

    var schema: [String: Any] {
        var criteria = [String: Any]()
        for id in Self.ids {
            let values = aliases[id] ?? []
            let abstain: [String: Any] = ["type": "object", "properties": [
                "anchor": ["type": "null"],
                "evidence": ["type": "array", "items": ["type": "string"], "maxItems": 0],
                "reason": ["type": "string", "pattern": #"^[^\u0000-\u001f]{8,60}$"#]
            ], "required": ["anchor", "evidence", "reason"], "additionalProperties": false]
            if values.isEmpty { criteria[id] = abstain; continue }
            let observed: [String: Any] = ["type": "object", "properties": [
                "anchor": ["type": "integer", "enum": id == "T01" && failedSQL ? [0] : [0, 1, 2, 3]],
                "evidence": ["type": "array", "items": ["type": "string", "enum": values], "minItems": 1, "maxItems": 4],
                "reason": ["type": "string", "pattern": #"^[^\u0000-\u001f]{8,60}$"#]
            ], "required": ["anchor", "evidence", "reason"], "additionalProperties": false]
            criteria[id] = ["anyOf": [abstain, observed]]
        }
        return ["type": "object", "properties": ["reply": [
            "type": "object", "properties": criteria,
            "required": Self.ids, "additionalProperties": false
        ]], "required": ["reply"], "additionalProperties": false]
    }

    func decode(_ value: Any?) throws -> String {
        guard let object = value as? [String: Any], Set(object.keys) == Set(Self.ids)
        else { throw TIAProviderFailure.invalidResponse }
        var rows = [[Any]]()
        for id in Self.ids {
            guard let row = object[id] as? [String: Any], Set(row.keys) == ["anchor", "evidence", "reason"],
                  let citations = row["evidence"] as? [String], citations.count <= 4,
                  Set(citations).count == citations.count, Set(citations).isSubset(of: Set(aliases[id] ?? [])),
                  let reason = row["reason"] as? String, (8...60).contains(reason.trimmingCharacters(in: .whitespacesAndNewlines).count),
                  !reason.unicodeScalars.contains(where: { $0.value < 32 })
            else { throw TIAProviderFailure.invalidResponse }
            let anchor: Any
            if row["anchor"] is NSNull {
                guard citations.isEmpty else { throw TIAProviderFailure.invalidResponse }
                anchor = NSNull()
            } else {
                guard let number = row["anchor"] as? NSNumber, CFGetTypeID(number) != CFBooleanGetTypeID(),
                      number.doubleValue == Double(number.intValue), (0...3).contains(number.intValue),
                      !citations.isEmpty, !(id == "T01" && failedSQL && number.intValue != 0)
                else { throw TIAProviderFailure.invalidResponse }
                anchor = number.intValue
            }
            rows.append([id, anchor, citations, reason])
        }
        let data = try JSONSerialization.data(withJSONObject: ["assessments": rows], options: [.sortedKeys, .withoutEscapingSlashes])
        guard let text = String(data: data, encoding: .utf8), text.count <= 2000, data.count <= 8000
        else { throw TIAProviderFailure.invalidResponse }
        return text
    }
}

struct TIAModelRequest {
    let transactionID: String
    let requestID: String
    let generation: String
    let role: String
    let instructions: String
    let input: String
    let schemaName: String
    let outputTokens: Int
    let promptSHA: String
    let sourceSHA: [String: String]
    let evaluatorContract: TIAEvaluatorReplyContract?

    init(_ value: [String: Any]) throws {
        let expected: Set<String> = ["schema_version", "transaction_id", "request_id", "generation", "role", "instructions", "input", "schema_name", "max_output_tokens", "prompt_sha256", "source_sha256"]
        func validID(_ value: String) -> Bool { value.range(of: "\\A[A-Za-z0-9_-]{1,80}\\z", options: .regularExpression) != nil }
        func digest(_ value: String) -> Bool { value.range(of: "\\A[a-f0-9]{64}\\z", options: .regularExpression) != nil }
        guard Set(value.keys) == expected, value["schema_version"] as? String == "tia-native-request/v1",
              let transactionID = value["transaction_id"] as? String, validID(transactionID),
              let requestID = value["request_id"] as? String, validID(requestID),
              let generation = value["generation"] as? String, validID(generation),
              let role = value["role"] as? String, ["interviewer", "trainer", "preparer", "evaluator"].contains(role),
              let instructions = value["instructions"] as? String, !instructions.isEmpty, instructions.utf8.count <= 32768,
              let input = value["input"] as? String, input.utf8.count <= 262144,
              let encoded = input.data(using: .utf8), let context = (try? StrictJSON.object(encoded)) as? [String: Any],
              input.utf8.count <= (role == "evaluator" && context["evidence_policy"] as? String == "tia-evaluator-evidence/v2"
                && context["continuity_policy"] as? String == "tia-continuity/v3" ? 262144 : 16000),
              let name = value["schema_name"] as? String, name == "tia_" + role + "_reply",
              let tokens = value["max_output_tokens"] as? NSNumber, CFGetTypeID(tokens) != CFBooleanGetTypeID(),
              let promptSHA = value["prompt_sha256"] as? String, digest(promptSHA),
              promptSHA == SHA256.hash(data: Data(instructions.utf8)).map({ String(format: "%02x", $0) }).joined(),
              let sourceSHA = value["source_sha256"] as? [String: String], (1...32).contains(sourceSHA.count),
              sourceSHA.allSatisfy({ key, hash in
                  !key.isEmpty && key.utf8.count <= 160 && !key.hasPrefix("/")
                    && !key.split(separator: "/").contains("..") && !key.contains("\\")
                    && !key.unicodeScalars.contains(where: { $0.value < 32 }) && digest(hash)
              }) else { throw TIAProviderFailure.invalidRequest }
        if let marker = context["response_contract"] {
            guard role == "evaluator", marker as? String == TIAEvaluatorReplyContract.version
            else { throw TIAProviderFailure.invalidRequest }
            guard tokens.doubleValue == 1600 else { throw TIAProviderFailure.invalidRequest }
            evaluatorContract = try TIAEvaluatorReplyContract(context: context)
        } else {
            guard tokens.doubleValue == Double(role == "preparer" ? 8192 : 600)
            else { throw TIAProviderFailure.invalidRequest }
            evaluatorContract = nil
        }
        self.transactionID = transactionID; self.requestID = requestID; self.generation = generation
        self.role = role; self.instructions = instructions; self.input = input
        self.schemaName = name; self.outputTokens = tokens.intValue
        self.promptSHA = promptSHA; self.sourceSHA = sourceSHA
    }
}

struct TIAProviderReply {
    let text: String
    let usage: [String: Int]?
    let responseID: String?
    var dictionary: [String: Any] {
        ["reply": text, "usage": usage as Any? ?? NSNull(), "response_id": responseID as Any? ?? NSNull()]
    }
}

final class TIAOpenAIAdapter: NSObject, URLSessionTaskDelegate, URLSessionDataDelegate {
    static let endpoint = URL(string: "https://api.openai.com/v1/responses")!
    static let maximumResponseBytes = 256 * 1024
    private let configuration: URLSessionConfiguration
    private let lock = NSLock()
    private var session: URLSession?
    private var task: URLSessionDataTask?
    private var completion: ((Result<TIAProviderReply, TIAProviderFailure>) -> Void)?
    private var received = Data()
    private var status = 0
    private var activeKey: String?
    private var activeResponseRole: String?
    private var activeResponseSpec: TIAModelRequest?

    init(configuration: URLSessionConfiguration = .ephemeral) {
        self.configuration = configuration.copy() as! URLSessionConfiguration
        super.init()
    }
    static func validModel(_ model: String) -> Bool {
        model.range(of: "\\A[A-Za-z0-9][A-Za-z0-9._-]{0,79}\\z", options: .regularExpression) != nil
    }
    static func request(key: String, model: String, spec: TIAModelRequest) throws -> URLRequest {
        guard NativePortal.validCredential(key), validModel(model), !model.contains(key) else { throw TIAProviderFailure.invalidConfiguration }
        // The provider cannot choose a different schema, tools, endpoint or budget.
        let schema: [String: Any] = spec.evaluatorContract?.schema ?? ["type": "object", "properties": ["reply": ["type": "string"]], "required": ["reply"], "additionalProperties": false]
        let body: [String: Any] = ["model": model, "instructions": spec.instructions, "input": spec.input,
            "max_output_tokens": spec.outputTokens, "store": false,
            "text": ["format": ["type": "json_schema", "name": spec.schemaName, "strict": true, "schema": schema]]]
        var request = URLRequest(url: endpoint, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 30)
        request.httpMethod = "POST"
        request.setValue("Bearer " + key, forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body, options: [.sortedKeys])
        guard request.httpBody!.count <= (spec.role == "evaluator" ? 2 * 1024 * 1024 : 65536) else { throw TIAProviderFailure.invalidRequest }
        return request
    }
    private static func httpFailure(_ data: Data, status: Int) -> TIAProviderFailure {
        // Only interpret a bounded allowlisted error code. Never surface provider error text.
        let object = (try? StrictJSON.object(data)) as? [String: Any]
        let error = object?["error"] as? [String: Any]
        let code = error?["code"] as? String
        if status == 401 { return .invalidCredentials }
        if status == 403 { return .permissionDenied }
        if status == 404 || code == "model_not_found" { return .modelUnavailable }
        if status == 429 {
            return ["insufficient_quota", "billing_hard_limit_reached"].contains(code ?? "") ? .usageLimit : .rateLimited
        }
        if (300...399).contains(status) { return .redirect }
        return .httpStatus(status)
    }
    static func parse(_ data: Data, status: Int, role: String = "interviewer", spec: TIAModelRequest? = nil) throws -> TIAProviderReply {
        guard spec == nil || spec?.role == role else { throw TIAProviderFailure.invalidResponse }
        guard ["interviewer", "trainer", "preparer", "evaluator"].contains(role),
              data.count <= maximumResponseBytes else { throw TIAProviderFailure.oversized }
        guard status == 200 else { throw httpFailure(data, status: status) }
        guard let body = try StrictJSON.object(data) as? [String: Any],
              let state = body["status"] as? String else { throw TIAProviderFailure.invalidResponse }
        guard state == "completed" else { throw TIAProviderFailure.incomplete }
        guard let output = body["output"] as? [[String: Any]] else { throw TIAProviderFailure.invalidResponse }
        var texts = [String]()
        for item in output {
            if item["type"] as? String == "refusal" { throw TIAProviderFailure.refused }
            if item["type"] as? String == "reasoning" { continue }
            guard item["type"] as? String == "message", item["role"] as? String == "assistant",
                  item["status"] as? String == "completed", let content = item["content"] as? [[String: Any]] else { throw TIAProviderFailure.invalidResponse }
            for part in content {
                if part["type"] as? String == "refusal" { throw TIAProviderFailure.refused }
                guard part["type"] as? String == "output_text", let text = part["text"] as? String else { throw TIAProviderFailure.invalidResponse }
                texts.append(text)
            }
        }
        let maxEncoded = role == "preparer" ? 131072 : 16384
        let maxChars = role == "preparer" ? 32768 : 2000
        let maxBytes = role == "preparer" ? 65536 : 8000
        guard texts.count == 1, let text = texts.first, text.utf8.count <= maxEncoded,
              let encoded = text.data(using: .utf8), let object = try StrictJSON.object(encoded) as? [String: Any],
              Set(object.keys) == ["reply"] else { throw TIAProviderFailure.invalidResponse }
        let reply: String
        if let contract = spec?.evaluatorContract {
            reply = try contract.decode(object["reply"])
        } else {
            guard let legacy = object["reply"] as? String else { throw TIAProviderFailure.invalidResponse }
            reply = legacy
        }
        guard !reply.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              reply.count <= maxChars, reply.utf8.count <= maxBytes else { throw TIAProviderFailure.invalidResponse }
        var usage: [String: Int]?
        if let raw = body["usage"], !(raw is NSNull) {
            guard let values = raw as? [String: Any] else { throw TIAProviderFailure.invalidResponse }
            var parsed = [String: Int]()
            for key in ["input_tokens", "output_tokens", "total_tokens"] {
                guard let value = values[key] as? NSNumber, CFGetTypeID(value) != CFBooleanGetTypeID(),
                      value.doubleValue >= 0, value.doubleValue <= 100_000_000,
                      value.doubleValue == Double(value.intValue) else { throw TIAProviderFailure.invalidResponse }
                parsed[key] = value.intValue
            }
            guard parsed["total_tokens"] == parsed["input_tokens"]! + parsed["output_tokens"]! else { throw TIAProviderFailure.invalidResponse }
            usage = parsed
        }
        var responseID: String?
        if let raw = body["id"] {
            guard let value = raw as? String, value.range(of: "\\A[A-Za-z0-9_-]{1,128}\\z", options: .regularExpression) != nil else { throw TIAProviderFailure.invalidResponse }
            responseID = value
        }
        return TIAProviderReply(text: reply, usage: usage, responseID: responseID)
    }
    func send(key: String, model: String, spec: TIAModelRequest, completion: @escaping (Result<TIAProviderReply, TIAProviderFailure>) -> Void) {
        let request: URLRequest
        do { request = try Self.request(key: key, model: model, spec: spec) }
        catch { DispatchQueue.main.async { completion(.failure((error as? TIAProviderFailure) ?? .invalidRequest)) }; return }
        lock.lock()
        guard self.completion == nil else { lock.unlock(); DispatchQueue.main.async { completion(.failure(.invalidRequest)) }; return }
        self.completion = completion; activeKey = key; activeResponseRole = spec.role
        activeResponseSpec = spec.evaluatorContract == nil ? nil : spec
        received = Data(); status = 0
        configuration.urlCache = nil; configuration.httpCookieStorage = nil; configuration.urlCredentialStorage = nil
        configuration.httpShouldSetCookies = false; configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 30; configuration.requestCachePolicy = .reloadIgnoringLocalCacheData
        session = URLSession(configuration: configuration, delegate: self, delegateQueue: nil)
        task = session!.dataTask(with: request)
        let active = task; lock.unlock(); active?.resume()
    }
    func cancel() {
        lock.lock()
        let current = task; let currentSession = session
        completion = nil; task = nil; session = nil; activeKey = nil; activeResponseRole = nil; activeResponseSpec = nil
        received = Data()
        lock.unlock(); current?.cancel(); currentSession?.invalidateAndCancel()
    }
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        completionHandler(nil)
        finish(.failure(.redirect), session: session)
    }
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse, completionHandler: @escaping (URLSession.ResponseDisposition) -> Void) {
        lock.lock(); let current = self.session === session; lock.unlock()
        guard current else { completionHandler(.cancel); return }
        guard response.url == Self.endpoint, let http = response as? HTTPURLResponse else {
            completionHandler(.cancel); finish(.failure(.invalidResponse), session: session); return
        }
        guard response.expectedContentLength <= Int64(Self.maximumResponseBytes) else {
            completionHandler(.cancel); finish(.failure(.oversized), session: session); return
        }
        lock.lock(); if self.session === session { status = http.statusCode }; lock.unlock()
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
        lock.lock(); let data = received; let code = status; let key = activeKey
        let spec = activeResponseSpec; let role = activeResponseRole; let current = self.session === session; lock.unlock()
        guard current else { return }
        if let error = error as NSError? {
            let failure: TIAProviderFailure = error.domain == NSURLErrorDomain && error.code == NSURLErrorTimedOut ? .timeout : .transport
            finish(.failure(failure), session: session); return
        }
        do {
            guard let role = role else { throw TIAProviderFailure.invalidResponse }
            let value: TIAProviderReply
            if let spec = spec {
                value = try Self.parse(data, status: code, role: role, spec: spec)
            } else {
                value = try Self.parse(data, status: code, role: role)
            }
            guard let key = key, !String(decoding: data, as: UTF8.self).contains(key),
                  !Self.containsSecret(value.dictionary, secret: key) else { throw TIAProviderFailure.invalidResponse }
            finish(.success(value), session: session)
        } catch { finish(.failure((error as? TIAProviderFailure) ?? .invalidResponse), session: session) }
    }
    static func containsSecret(_ value: Any, secret: String) -> Bool {
        if let text = value as? String { return text.contains(secret) }
        if let values = value as? [Any] { return values.contains { containsSecret($0, secret: secret) } }
        if let object = value as? [String: Any] { return object.contains { $0.key.contains(secret) || containsSecret($0.value, secret: secret) } }
        return false
    }
    private func finish(_ result: Result<TIAProviderReply, TIAProviderFailure>, session: URLSession) {
        lock.lock()
        guard self.session === session else { lock.unlock(); return }
        let callback = completion
        completion = nil; task = nil; self.session = nil; activeKey = nil; activeResponseRole = nil; activeResponseSpec = nil
        received = Data()
        lock.unlock(); session.invalidateAndCancel()
        DispatchQueue.main.async { callback?(result) }
    }
}
