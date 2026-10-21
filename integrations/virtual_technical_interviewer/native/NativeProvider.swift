import Foundation

// Native memory only. Every method is called on the AppKit/main thread; transport
// completion returns there too. No credential-bearing value is exported.
final class NativePortal {
    private let adapter: TIAOpenAIAdapter
    private var credential: String?
    private var paidConsent = false
    private var verified = false
    private var usedRequestIDs = Set<String>()
    private var activeRequestID: String?
    private var lastFailure: TIAProviderFailure?
    private var measuredUsage = ["input_tokens": 0, "output_tokens": 0, "total_tokens": 0]
    private var usageResponses = 0
    private var responsesWithoutUsage = 0
    private(set) var state = "offline"
    private(set) var generation = UUID().uuidString
    private(set) var requestsUsed = 0
    private(set) var requestsTotal = 0
    private(set) var requestLimit = 0
    private(set) var model = "gpt-4.1-mini"

    init(adapter: TIAOpenAIAdapter = TIAOpenAIAdapter()) { self.adapter = adapter }
    static func validCredential(_ key: String) -> Bool {
        (16...1024).contains(key.utf8.count) && key.unicodeScalars.allSatisfy { (33...126).contains($0.value) }
    }
    // Compatibility with S03-B's unpaid local configuration; this grants no calls.
    @discardableResult func configure(_ key: String, consent: Bool) -> Bool {
        guard consent, Self.validCredential(key) else { return false }
        disconnect(); credential = key; state = "activated-unverified"
        return true
    }
    @discardableResult func activate(key: String, model: String, requestLimit: Int, paidConsent: Bool) -> Bool {
        guard paidConsent, Self.validCredential(key), TIAOpenAIAdapter.validModel(model), !model.contains(key), (1...20).contains(requestLimit) else { return false }
        disconnect(); self.credential = key; self.model = model; self.requestLimit = requestLimit
        self.requestsUsed = 0; usedRequestIDs.removeAll()
        self.paidConsent = true; state = "activated-unverified"
        return true
    }
    func send(_ spec: TIAModelRequest, completion: @escaping (Result<TIAProviderReply, TIAProviderFailure>) -> Void) {
        let failure: TIAProviderFailure?
        if credential == nil { failure = .notActivated }
        else if !paidConsent { failure = .consentRequired }
        else if activeRequestID != nil || spec.generation != generation || usedRequestIDs.contains(spec.requestID) { failure = .invalidRequest }
        else if requestsUsed >= requestLimit { failure = .budgetExceeded }
        else { failure = nil }
        if let failure = failure {
            DispatchQueue.main.async { completion(.failure(failure)) }
            return
        }
        guard let key = credential else { return }
        // Reject malformed/oversized bodies before consuming an HTTP attempt.
        do { _ = try TIAOpenAIAdapter.request(key: key, model: model, spec: spec) }
        catch {
            DispatchQueue.main.async { completion(.failure((error as? TIAProviderFailure) ?? .invalidRequest)) }
            return
        }
        let token = generation
        requestsUsed += 1; requestsTotal += 1; usedRequestIDs.insert(spec.requestID); activeRequestID = spec.requestID
        lastFailure = nil; state = "connecting"
        adapter.send(key: key, model: model, spec: spec) { [weak self] result in
            guard let self = self, self.generation == token, self.activeRequestID == spec.requestID,
                  self.credential != nil, self.paidConsent else { return }
            self.activeRequestID = nil
            switch result {
            case .success(let reply):
                self.verified = true; self.state = "live-verified"; self.lastFailure = nil
                if let usage = reply.usage {
                    for (key, amount) in usage { self.measuredUsage[key, default: 0] += amount }
                    self.usageResponses += 1
                } else { self.responsesWithoutUsage += 1 }
            case .failure(let error):
                self.lastFailure = error; self.state = "unavailable"
                if case .invalidCredentials = error {
                    self.credential = nil; self.paidConsent = false; self.verified = false
                }
            }
            completion(result)
        }
    }
    func cancel() {
        generation = UUID().uuidString; activeRequestID = nil; adapter.cancel(); lastFailure = nil
        state = credential == nil ? "offline" : (verified ? "live-verified" : "activated-unverified")
    }
    func disconnect() {
        cancel(); credential = nil; paidConsent = false; verified = false; state = "offline"
        // Retain attempt/usage history until app exit; disconnect must not erase cost evidence.
        lastFailure = nil
    }
    var publicState: [String: Any] {
        ["state": state, "requests_used": requestsUsed, "request_limit": requestLimit,
         "requests_total": requestsTotal, "usage_scope": "APP_PROCESS_MEASURED_RESPONSES",
         "requests_without_measured_usage": requestsTotal - usageResponses,
         "live_enabled": credential != nil && paidConsent, "authenticated": verified && credential != nil,
         "provider": "OpenAI", "model": model, "paid_consent": paidConsent,
         "usage": usageResponses > 0 ? measuredUsage as Any : NSNull(),
         "usage_responses": usageResponses, "responses_without_usage": responsesWithoutUsage,
         "error_code": lastFailure?.code as Any? ?? NSNull(),
         "error_message": lastFailure?.publicMessage as Any? ?? NSNull(),
         "reason": lastFailure?.code ?? (paidConsent ? "EXPLICIT_PAID_CONSENT" : "PAID_CONSENT_REQUIRED")]
    }
}
