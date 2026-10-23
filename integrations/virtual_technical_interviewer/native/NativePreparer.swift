import Foundation
import CryptoKit

// E4-C1B: Native-only, session-memory reference proposal boundary.
// No solution is written to Python journal, WebKit, export, or interviewer input.
enum TIAPreparerError: Error {
    case invalidSetup, inputTooLarge, invalidModelResponse
}

struct TIAPreparerPackage {
    let binding: String
    let questionCount: Int
    let questionSetSHA: String
    let questions: [[String: String]]
    let input: String

    static func sha(_ text: String) -> String {
        SHA256.hash(data: Data(text.utf8)).map { String(format: "%02x", $0) }.joined()
    }
    static func encoded(_ object: Any) throws -> String {
        guard JSONSerialization.isValidJSONObject(object),
              let data = try? JSONSerialization.data(withJSONObject: object, options: [.sortedKeys, .withoutEscapingSlashes]),
              let value = String(data: data, encoding: .utf8) else { throw TIAPreparerError.invalidSetup }
        return value
    }
    init(state: [String: Any]) throws {
        guard state["screen"] as? String == "REVIEW",
              let pf = state["preflight_readiness"] as? [String: Any],
              pf["schema"] as? String == "tia-preflight-readiness/v1",
              pf["status"] as? String == "READY_FOR_FUTURE_PRIVATE_PREPARATION",
              let reports = pf["questions"] as? [[String: Any]],
              let reviews = state["setup_questions"] as? [[String: Any]],
              (3...4).contains(reports.count), reports.count == reviews.count,
              pf["required_count"] as? Int == reports.count else { throw TIAPreparerError.invalidSetup }
        var bound = [[String: Any]]()
        var modelQuestions = [[String: Any]]()
        var validatedQuestions = [[String: String]]()
        var hashes = Set<String>()
        let required = ["problem_statement", "task", "schema", "example_input", "expected_output", "environment", "source"]
        for index in reports.indices {
            let report = reports[index]
            let review = reviews[index]
            guard report["status"] as? String == "SOURCE_BOUND_CONFIRMED",
                  report["question_index"] as? Int == index,
                  review["human_confirmed"] as? Bool == true,
                  review["practice_eligible"] as? Bool == true,
                  let hash = report["question_sha256"] as? String,
                  hash.range(of: "\\A[0-9a-f]{64}\\z", options: .regularExpression) != nil,
                  review["content_sha256"] as? String == hash,
                  hashes.insert(hash).inserted,
                  let env = report["environment"] as? String,
                  ["POSTGRESQL", "PANDAS"].contains(env),
                  let fields = review["fields"] as? [String: String],
                  fields["environment"] == env,
                  required.allSatisfy({ fields[$0] != nil }) else { throw TIAPreparerError.invalidSetup }
            let source = ["question_sha256": hash, "environment": env]
            bound.append(["index": index, "question_sha256": hash, "environment": env])
            validatedQuestions.append(source)
            modelQuestions.append(["index": index, "question_sha256": hash, "fields": fields])
        }
        let bindingObject: [String: Any] = ["schema": "tia-private-prep-binding/v1", "questions": bound]
        let sha = Self.sha(try Self.encoded(bindingObject))
        let packet: [String: Any] = ["schema": "tia-native-private-preparer-input/v1",
                                     "question_set_sha256": sha, "questions": modelQuestions,
                                     "authority": "UNTRUSTED_QUESTION_DATA_ONLY",
                                     "execution_status": "NOT_RUN"]
        let content = try Self.encoded(packet)
        if content.utf8.count > 16000 { throw TIAPreparerError.inputTooLarge }
        self.binding = try Self.encoded(bindingObject)
        self.questionSetSHA = sha
        self.questions = validatedQuestions
        self.questionCount = reports.count
        self.input = content
    }

    func validate(_ response: String) throws -> TIAPreparerSeal {
        guard response.utf8.count <= 65536, let data = response.data(using: .utf8),
              let root = try? StrictJSON.object(data) as? [String: Any],
              Set(root.keys) == Set(["schema", "question_set_sha256", "items"]),
              root["schema"] as? String == "tia-preparer-model-proposal/v1",
              root["question_set_sha256"] as? String == questionSetSHA,
              let items = root["items"] as? [[String: Any]], items.count == questionCount
        else { throw TIAPreparerError.invalidModelResponse }
        for index in items.indices {
            let item = items[index], source = questions[index]
            guard Set(item.keys) == Set(["question_sha256", "language", "approaches"]),
                  item["question_sha256"] as? String == source["question_sha256"],
                  item["language"] as? String == source["environment"],
                  let approaches = item["approaches"] as? [[String: Any]],
                  (1...3).contains(approaches.count) else { throw TIAPreparerError.invalidModelResponse }
            for approach in approaches {
                guard Set(approach.keys) == Set(["label", "code", "rationale", "invariants", "edge_cases", "complexity"]) else {
                    throw TIAPreparerError.invalidModelResponse
                }
                for (field, limit) in [("label", 100), ("code", 8192), ("rationale", 1800), ("complexity", 500)] {
                    guard let value = approach[field] as? String, !value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                          !value.contains("\0"), value.utf8.count <= limit else { throw TIAPreparerError.invalidModelResponse }
                }
                for field in ["invariants", "edge_cases"] {
                    guard let entries = approach[field] as? [String], (1...6).contains(entries.count),
                          entries.allSatisfy({ !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !$0.contains("\0") && $0.utf8.count <= 500 })
                    else { throw TIAPreparerError.invalidModelResponse }
                }
            }
        }
        return TIAPreparerSeal(questionSetSHA: questionSetSHA, count: questionCount, privateRawProposal: response)
    }
}

// Native-process private memory only. This is not persisted across app restarts.
final class TIAPreparerSeal {
    let questionSetSHA: String
    let count: Int
    private let privateRawProposal: String
    init(questionSetSHA: String, count: Int, privateRawProposal: String) {
        self.questionSetSHA = questionSetSHA
        self.count = count
        self.privateRawProposal = privateRawProposal
    }
    var safeStatus: [String: Any] {
        ["status": "REFERENCE_UNVERIFIED_AI_PROPOSAL", "question_set_sha256": questionSetSHA,
         "question_count": count, "execution_status": "NOT_RUN", "technical": "NOT_SCORED",
         "interviewer_reference_access": false, "persistence": "NATIVE_MEMORY_ONLY"]
    }
}
