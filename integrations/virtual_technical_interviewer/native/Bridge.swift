import Foundation
import CoreFoundation
import Darwin

enum PrivateExport {
    // Native Save-panel destinations only. The temporary file is private before
    // any transcript bytes are written, then atomically replaces the chosen file.
    static func write(_ data: Data, to url: URL) throws {
        guard url.isFileURL, !url.hasDirectoryPath,
              !((try? url.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink) ?? false)
        else { throw CocoaError(.fileWriteNoPermission) }
        let temporary = url.deletingLastPathComponent().appendingPathComponent(".tia-export-" + UUID().uuidString)
        let fd = Darwin.open(temporary.path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0o600)
        guard fd >= 0 else { throw CocoaError(.fileWriteNoPermission) }
        let handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
        defer { try? handle.close(); try? FileManager.default.removeItem(at: temporary) }
        try handle.write(contentsOf: data)
        try handle.synchronize()
        guard Darwin.rename(temporary.path, url.path) == 0 else { throw CocoaError(.fileWriteUnknown) }
    }
}

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
        "export", "api_portal", "disconnect", "setup_continue", "setup_back", "setup_launch",
        "preview_verify", "preview_close", "preview_cancel", "trainer_request", "rehearsal_start", "rehearsal_submit", "rehearsal_skip", "rehearsal_tick"
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
              data.count <= 32768 else { return nil }
        if emptyActions.contains(action) {
            guard params.isEmpty else { return nil }
        } else if action == "grade_inspect" {
            guard Set(params.keys) == ["fixture_json"],
                  let fixture = params["fixture_json"] as? String,
                  !fixture.isEmpty, fixture.utf8.count <= 12000 else { return nil }
        } else if action == "grade_execute" {
            guard Set(params.keys) == ["fixture_sha256"],
                  let digest = params["fixture_sha256"] as? String,
                  digest.range(of: "\\A[0-9a-f]{64}\\z", options: .regularExpression) != nil else { return nil }
        } else if action == "language" {
            guard Set(params.keys) == ["language"], let lang = params["language"] as? String,
                  ["en", "zh"].contains(lang) else { return nil }
        } else if action == "tutorial_submit" || action == "preview_send" {
            guard Set(params.keys) == ["kind", "text"],
                  let kind = params["kind"] as? String,
                  (action == "preview_send" ? ["clarify", "plan", "implement", "help"] : ["clarify", "plan", "implement", "test", "help"]).contains(kind),
                  let text = params["text"] as? String,
                  !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                  text.utf8.count <= (action == "preview_send" ? 4096 : 8192) else { return nil }
        } else if action == "setup_config" {
            guard Set(params.keys) == ["config"], let config = params["config"] as? [String: Any],
                  Set(config.keys) == ["technical_environment", "duration_minutes", "difficulty", "question_source", "interviewer_mechanism"],
                  let env = config["technical_environment"] as? String, ["POSTGRESQL", "PANDAS"].contains(env),
                  let duration = config["duration_minutes"] as? NSNumber,
                  CFGetTypeID(duration) != CFBooleanGetTypeID(), [45, 60].contains(duration.intValue),
                  duration.doubleValue == Double(duration.intValue),
                  config["difficulty"] as? String == "HARD",
                  let source = config["question_source"] as? String, ["BYOQ", "RANDOM_GENERATED"].contains(source),
                  let mechanism = config["interviewer_mechanism"] as? String,
                  ["STRICT_CHALLENGING", "PROFESSIONAL_SUPPORTIVE"].contains(mechanism) else { return nil }
        } else if action == "setup_questions" {
            guard Set(params.keys) == ["questions"], let questions = params["questions"] as? [String],
                  questions.count <= 4, questions.allSatisfy({ $0.utf8.count <= 4096 }) else { return nil }
        } else if action == "setup_question_set" {
            guard Set(params.keys) == ["index", "raw_text", "source"],
                  let index = params["index"] as? NSNumber,
                  CFGetTypeID(index) != CFBooleanGetTypeID(), index.intValue >= 0, index.intValue < 4,
                  index.doubleValue == Double(index.intValue),
                  let raw = params["raw_text"] as? String, !raw.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                  raw.utf8.count <= 8192,
                  let source = params["source"] as? String,
                  ["LEETCODE", "HACKERRANK", "OWNER"].contains(source) else { return nil }
        } else if action == "setup_question_confirm" {
            guard Set(params.keys) == ["index", "fields", "raw_sha256"],
                  let index = params["index"] as? NSNumber,
                  CFGetTypeID(index) != CFBooleanGetTypeID(), index.intValue >= 0, index.intValue < 4,
                  index.doubleValue == Double(index.intValue),
                  let fields = params["fields"] as? [String: Any],
                  Set(fields.keys) == ["problem_statement", "task", "schema", "example_input", "expected_output",
                                       "environment", "source", "constraints", "source_reference"],
                  fields.values.allSatisfy({ value in guard let text = value as? String else { return false }; return text.utf8.count <= 8192 }),
                  let digest = params["raw_sha256"] as? String,
                  digest.range(of: "\\A[0-9a-f]{64}\\z", options: .regularExpression) != nil else { return nil }
        } else if action == "practice_start" {
            guard Set(params.keys) == ["index", "content_sha256"],
                  let index = params["index"] as? NSNumber,
                  CFGetTypeID(index) != CFBooleanGetTypeID(), index.intValue >= 0, index.intValue < 4,
                  index.doubleValue == Double(index.intValue),
                  let digest = params["content_sha256"] as? String,
                  digest.range(of: "\\A[0-9a-f]{64}\\z", options: .regularExpression) != nil else { return nil }
        } else if action == "setup_questions_finish" {
            guard params.isEmpty else { return nil }
        } else if action == "setup_mechanism" {
            guard Set(params.keys) == ["mechanism"], let mechanism = params["mechanism"] as? String,
                  ["STRICT_CHALLENGING", "PROFESSIONAL_SUPPORTIVE"].contains(mechanism) else { return nil }
        } else { return nil }
        return (id, action, params)
    }
}
