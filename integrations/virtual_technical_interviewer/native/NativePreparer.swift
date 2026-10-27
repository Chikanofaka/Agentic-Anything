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
        return TIAPreparerSeal(questionSetSHA: questionSetSHA, count: questionCount, privateRawProposal: response, questionSources: questions)
    }
}

// Native-process private memory only. This is not persisted across app restarts.
final class TIAPreparerSeal {
    let questionSetSHA: String
    let count: Int
    private let privateRawProposal: String
    private let questionSources: [[String: String]]
    private var verificationReceipts: [Int: [String: Any]] = [:]
    private var verificationProcess: Process?
    private var verificationGeneration = UUID()
    var isVerifying: Bool { verificationProcess != nil }

    init(questionSetSHA: String, count: Int, privateRawProposal: String,
         questionSources: [[String: String]]) {
        self.questionSetSHA = questionSetSHA
        self.count = count
        self.privateRawProposal = privateRawProposal
        self.questionSources = questionSources
    }

    // Native UI selects an owner-approved fixture; no reference getter exists.
    // Only the reviewed one-shot verifier receives reference code, over stdin.
    // The regular Python controller/Worker and WebKit never receive this packet.
    @discardableResult
    func verifyReference(questionIndex: Int, fixture: Data, approvalSHA: String,
                         runtime: URL, completion: @escaping ([String: Any]) -> Void) -> Bool {
        guard !isVerifying, questionSources.indices.contains(questionIndex),
              questionSources[questionIndex]["environment"] == "POSTGRESQL",
              !fixture.isEmpty, fixture.count <= 262144,
              SHA256.hash(data: fixture).map({ String(format: "%02x", $0) }).joined() == approvalSHA,
              let fixtureText = String(data: fixture, encoding: .utf8),
              let fixtureObject = try? StrictJSON.object(fixture) as? [String: Any],
              fixtureObject["question_sha256"] as? String == questionSources[questionIndex]["question_sha256"],
              let proposalData = privateRawProposal.data(using: .utf8),
              let proposal = try? StrictJSON.object(proposalData) as? [String: Any],
              let items = proposal["items"] as? [[String: Any]], items.indices.contains(questionIndex),
              let approaches = items[questionIndex]["approaches"] as? [[String: Any]],
              (1...3).contains(approaches.count),
              Bundle.main.object(forInfoDictionaryKey: "TIADevelopmentBuild") as? Bool == true
        else { return false }
        let references = approaches.compactMap { $0["code"] as? String }
        guard references.count == approaches.count else { return false }
        let packet: [String: Any] = ["schema": "tia-private-oracle-request/v1",
            "question_sha256": questionSources[questionIndex]["question_sha256"]!,
            "fixture_json": fixtureText, "approval_sha256": approvalSHA, "references": references]
        guard let encoded = try? JSONSerialization.data(withJSONObject: packet), encoded.count <= 400000 else { return false }
        let process = Process(), stdin = Pipe(), stdout = Pipe()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        process.arguments = ["-B", "-u", "-m", "tia_runtime.private_oracle_worker"]
        process.currentDirectoryURL = runtime
        process.environment = ["PATH": "/usr/bin:/bin", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"]
        process.standardInput = stdin
        process.standardOutput = stdout
        process.standardError = FileHandle.nullDevice
        do { try process.run() } catch { return false }
        let generation = UUID()
        verificationGeneration = generation
        verificationProcess = process
        let referenceHashes = references.map(TIAPreparerPackage.sha)
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            var replyData = Data()
            do {
                try stdin.fileHandleForWriting.write(contentsOf: encoded)
                try stdin.fileHandleForWriting.close()
                while replyData.count <= 16384 {
                    let chunk = try stdout.fileHandleForReading.read(upToCount: 16385 - replyData.count) ?? Data()
                    if chunk.isEmpty { break }
                    replyData.append(chunk)
                }
                if replyData.count > 16384, process.isRunning { process.terminate() }
            } catch { if process.isRunning { process.terminate() } }
            process.waitUntilExit()
            DispatchQueue.main.async { [weak self] in
                guard let self = self, self.verificationGeneration == generation else { return }
                self.verificationProcess = nil
                var safe: [String: Any] = ["status": "REFERENCE_NOT_VERIFIED", "error": "ORACLE_VERIFICATION_FAILED"]
                if process.terminationStatus == 0, replyData.count <= 16384,
                   let result = try? StrictJSON.object(replyData) as? [String: Any],
                   Set(result.keys) == Set(["schema", "question_sha256", "fixture_sha256", "source", "official_hidden_tests", "references"]),
                   result["schema"] as? String == "tia-private-oracle-result/v1",
                   result["question_sha256"] as? String == self.questionSources[questionIndex]["question_sha256"],
                   result["fixture_sha256"] as? String == approvalSHA,
                   result["source"] as? String == "EPHEMERAL_POSTGRESQL_LOCAL",
                   result["official_hidden_tests"] as? Bool == false,
                   let rows = result["references"] as? [[String: Any]], rows.count == referenceHashes.count,
                   rows.enumerated().allSatisfy({ index, row in
                       Set(row.keys) == Set(["index", "reference_sha256", "status", "error"])
                       && row["index"] as? Int == index
                       && row["reference_sha256"] as? String == referenceHashes[index]
                       && ["PASSED", "FAILED", "EXECUTION_ERROR", "NOT_VERIFIED"].contains(row["status"] as? String ?? "")
                   }) {
                    let passed = rows.filter { $0["status"] as? String == "PASSED" }.count
                    let executed = rows.filter { $0["status"] as? String != "NOT_VERIFIED" }.count
                    // No free-form runner error, code, fixture rows or SQL output leaves this boundary.
                    safe = ["status": passed == rows.count ? "REFERENCE_VERIFIED_LOCAL_FIXTURE" : "REFERENCE_NOT_VERIFIED",
                            "question_sha256": self.questionSources[questionIndex]["question_sha256"]!,
                            "fixture_sha256": approvalSHA, "approaches_tested": executed,
                            "approaches_passed": passed, "approaches_total": rows.count,
                            "execution_status": executed > 0 ? "LOCAL_FIXTURE_RUN" : "NOT_RUN",
                            "official_hidden_tests": false]
                    self.verificationReceipts[questionIndex] = safe
                }
                self.verificationReceipts[questionIndex] = safe
                completion(safe)
            }
        }
        // Three independently proposed approaches, each protected by the existing
        // initdb/pg_ctl/query timeouts. Cancellation unwinds the Python cleanup.
        DispatchQueue.main.asyncAfter(deadline: .now() + 360) { [weak self] in
            guard let self = self, self.verificationGeneration == generation,
                  let running = self.verificationProcess, running.isRunning else { return }
            running.terminate()
        }
        return true
    }

    func cancelVerification() {
        verificationGeneration = UUID()
        if let process = verificationProcess, process.isRunning { process.terminate() }
        verificationProcess = nil
    }

    deinit { if let process = verificationProcess, process.isRunning { process.terminate() } }

    var safeStatus: [String: Any] {
        let verified = verificationReceipts.values.filter { $0["status"] as? String == "REFERENCE_VERIFIED_LOCAL_FIXTURE" }.count
        return ["status": verified == count ? "REFERENCE_VERIFIED_LOCAL_FIXTURE" : "REFERENCE_UNVERIFIED_AI_PROPOSAL",
         "question_set_sha256": questionSetSHA, "question_count": count,
         "execution_status": verificationReceipts.isEmpty ? "NOT_RUN" : "SEE_QUESTION_RESULTS",
         "technical": "NOT_SCORED", "interviewer_reference_access": false,
         "persistence": "NATIVE_MEMORY_ONLY", "verification_pending": isVerifying,
         "verified_questions": verified,
         "questions": questionSources.enumerated().map { index, source -> [String: Any] in
             var row: [String: Any] = verificationReceipts[index] ?? ["status": "REFERENCE_UNVERIFIED_AI_PROPOSAL", "execution_status": "NOT_RUN"]
             row["index"] = index
             row["question_sha256"] = source["question_sha256"]
             row["environment"] = source["environment"]
             return row
         }]
    }
}
