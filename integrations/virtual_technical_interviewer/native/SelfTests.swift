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
    check("E3D exact SMART start", BridgePolicy.validate(request("smart_start")) != nil)
    check("E3D SMART start cannot inject time", BridgePolicy.validate(request("smart_start", ["clock": 999])) == nil)
    let smartSample: [String: Any] = ["task_id": "SMART-Q1-TESTING_PRACTICE", "kind": "PRACTICED", "note": "Reviewed a tie case", "artifact_sha256": NSNull()]
    check("E3D exact SMART activity", BridgePolicy.validate(request("smart_record", smartSample)) != nil)
    check("E3D never accept renderer competence grade", BridgePolicy.validate(request("smart_record", smartSample.merging(["score": 100]) { _, extra in extra })) == nil)
    let smartRetest: [String: Any] = ["task_id": "SMART-Q1-TESTING_PRACTICE", "kind": "RETEST_RECORDED", "note": "External retest attempt", "artifact_sha256": String(repeating: "b", count: 64)]
    check("E3D self-reported artifact hash is bounded", BridgePolicy.validate(request("smart_record", smartRetest)) != nil)
    check("E3D cannot claim retest without artifact", BridgePolicy.validate(request("smart_record", smartRetest.merging(["artifact_sha256": NSNull()]) { _, extra in extra })) == nil)
    check("E3D invalid SMART task id rejected", BridgePolicy.validate(request("smart_record", smartSample.merging(["task_id": "../../fixture"]) { _, extra in extra })) == nil)
    check("E3D oversized SMART note rejected", BridgePolicy.validate(request("smart_record", smartSample.merging(["note": String(repeating: "中", count: 168)]) { _, extra in extra })) == nil)
    check("E3CB exact user trainer request", BridgePolicy.validate(request("trainer_request")) != nil)
    check("E4C1B exact Native preparer request", BridgePolicy.validate(request("preparer_request")) != nil)
    check("E4C1B renderer cannot forge private proposal", BridgePolicy.validate(request("preparer_request", ["code": "SELECT secret"])) == nil)
    check("E3CB renderer cannot send trainer feedback", BridgePolicy.validate(request("trainer_request", ["proposal": "approved"])) == nil)
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
    let config: [String: Any] = ["technical_environment": "POSTGRESQL", "duration_minutes": 45,
                                "difficulty": "HARD", "question_source": "BYOQ",
                                "interviewer_mechanism": "STRICT_CHALLENGING"]
    check("typed setup accepted", BridgePolicy.validate(request("setup_config", ["config": config])) != nil)
    var invalid = config; invalid["duration_minutes"] = true
    check("boolean duration rejected", BridgePolicy.validate(request("setup_config", ["config": invalid])) == nil)
    invalid = config; invalid["question_count"] = 4
    check("independent question count rejected", BridgePolicy.validate(request("setup_config", ["config": invalid])) == nil)
    invalid = config; invalid["difficulty"] = "EASY"
    check("Easy configuration rejected", BridgePolicy.validate(request("setup_config", ["config": invalid])) == nil)
    check("bounded question slots", BridgePolicy.validate(request("setup_questions", ["questions": Array(repeating: "x", count: 5)])) == nil)
    check("bounded pasted bytes", BridgePolicy.validate(request("setup_questions", ["questions": [String(repeating: "中", count: 1366)]])) == nil)
    let syntheticRaw = "Write a solution.\nTable: Scores\n| id | int |"
    check("S03D raw question accepted", BridgePolicy.validate(request("setup_question_set", ["index": 0, "raw_text": syntheticRaw, "source": "LEETCODE"])) != nil)
    check("S03D source must be approved", BridgePolicy.validate(request("setup_question_set", ["index": 0, "raw_text": syntheticRaw, "source": "SCRAPE_URL"])) == nil)
    check("S03D boolean index rejected", BridgePolicy.validate(request("setup_question_set", ["index": true, "raw_text": syntheticRaw, "source": "LEETCODE"])) == nil)
    check("S03D exact 8192-byte source accepted", BridgePolicy.validate(request("setup_question_set", ["index": 0, "raw_text": String(repeating: "中", count: 2730), "source": "OWNER"])) != nil)
    check("S03D excessive UTF8 source rejected", BridgePolicy.validate(request("setup_question_set", ["index": 0, "raw_text": String(repeating: "中", count: 2731), "source": "OWNER"])) == nil)
    check("S03D no extra authority in import", BridgePolicy.validate(request("setup_question_set", ["index": 0, "raw_text": syntheticRaw, "source": "OWNER", "grant": "SCORE"])) == nil)
    let digest = String(repeating: "a", count: 64)
    let edited: [String: Any] = ["problem_statement": "Find a solution", "task": "Return ids", "schema": "Scores(id INT)",
                                 "example_input": "", "expected_output": "", "environment": "POSTGRESQL", "source": "OWNER",
                                 "constraints": "", "source_reference": ""]
    check("S03D human-reviewed fields accepted", BridgePolicy.validate(request("setup_question_confirm", ["index": 0, "fields": edited, "raw_sha256": digest])) != nil)
    check("S03D fields cannot grant scores", BridgePolicy.validate(request("setup_question_confirm", ["index": 0, "fields": edited.merging(["scoring_authorized": true]) { _, extra in extra }, "raw_sha256": digest])) == nil)
    check("S03D practice digest accepted", BridgePolicy.validate(request("practice_start", ["index": 0, "content_sha256": digest])) != nil)
    check("S03D practice cannot override role", BridgePolicy.validate(request("practice_start", ["index": 0, "content_sha256": digest, "role": "admin"])) == nil)
    check("S03D exact finish command", BridgePolicy.validate(request("setup_questions_finish")) != nil)
    check("S03D finish rejects extra fields", BridgePolicy.validate(request("setup_questions_finish", ["bypass": true])) == nil)
    for action in ["native_prepare_preview", "native_commit_preview", "native_cancel_preview",
                   "native_prepare_trainer", "native_commit_trainer", "native_cancel_trainer"] {
        check("native-only handshake " + action, BridgePolicy.validate(request(action)) == nil)
    }
    check("bounded preview input", BridgePolicy.validate(request("preview_send", ["kind": "plan", "text": "one row per customer"])) != nil)
    check("preview cannot issue test execution", BridgePolicy.validate(request("preview_send", ["kind": "test", "text": "run"])) == nil)
    check("preview cannot inject mechanism or authority", BridgePolicy.validate(request("preview_send", ["kind": "plan", "text": "x", "mechanism": "STRICT_CHALLENGING"])) == nil)
    // E2.5-B: exact renderer contract, with native confirmation in main.swift.
    check("E25B inspect bounded fixture", BridgePolicy.validate(request("grade_inspect", ["fixture_json": "{\"x\":1}"])) != nil)
    check("E25B inspect rejects empty", BridgePolicy.validate(request("grade_inspect", ["fixture_json": ""])) == nil)
    check("E25B inspect rejects over-limit UTF8", BridgePolicy.validate(request("grade_inspect", ["fixture_json": String(repeating: "中", count: 4001)])) == nil)
    check("E25B inspect cannot grant authority", BridgePolicy.validate(request("grade_inspect", ["fixture_json": "{}", "admin": true])) == nil)
    check("E25B execute exact SHA", BridgePolicy.validate(request("grade_execute", ["fixture_sha256": digest])) != nil)
    check("E25B execute rejects invalid SHA", BridgePolicy.validate(request("grade_execute", ["fixture_sha256": "not-a-hash"])) == nil)
    check("E25B execute rejects path injection", BridgePolicy.validate(request("grade_execute", ["fixture_sha256": digest, "fixture_path": "/tmp/other.db"])) == nil)
    check("E25B native-only execution commit rejected", BridgePolicy.validate(request("native_commit_grade", ["status": "PASSED"])) == nil)
    // C1B Native-parser tests: 3 bound questions, wrong SHA, and injected grades.
    let syntheticHashes = [String(repeating: "a", count: 64), String(repeating: "b", count: 64), String(repeating: "c", count: 64)]
    let prepFields: [String: String] = ["problem_statement": "Find rows", "task": "Return ids",
        "schema": "Orders(id INT)", "example_input": "(1)", "expected_output": "1",
        "environment": "POSTGRESQL", "source": "OWNER"]
    let prepReports: [[String: Any]] = syntheticHashes.enumerated().map { index, hash in
        ["question_index": index, "question_sha256": hash, "environment": "POSTGRESQL", "status": "SOURCE_BOUND_CONFIRMED"]
    }
    let prepReviews: [[String: Any]] = syntheticHashes.map { hash in
        ["human_confirmed": true, "practice_eligible": true, "content_sha256": hash, "fields": prepFields]
    }
    let prepState: [String: Any] = ["screen": "REVIEW", "preflight_readiness": [
        "schema": "tia-preflight-readiness/v1", "status": "READY_FOR_FUTURE_PRIVATE_PREPARATION",
        "required_count": 3, "questions": prepReports], "setup_questions": prepReviews]
    let prep = try? TIAPreparerPackage(state: prepState)
    check("E4C1B source-bound 3 question preflight", prep?.questionCount == 3)
    if let prep = prep {
        let approach: [String: Any] = ["label": "group", "code": "SELECT id FROM Orders",
            "rationale": "Aggregate rows", "invariants": ["one row"],
            "edge_cases": ["empty"], "complexity": "linear"]
        let items: [[String: Any]] = syntheticHashes.map { hash in
            ["question_sha256": hash, "language": "POSTGRESQL", "approaches": [approach]]
        }
        let proposed: [String: Any] = ["schema": "tia-preparer-model-proposal/v1",
            "question_set_sha256": prep.questionSetSHA, "items": items]
        let candidate = try? TIAPreparerPackage.encoded(proposed)
        let validated = candidate.flatMap { try? prep.validate($0) }
        check("E4C1B native private proposal validated", validated?.safeStatus["question_count"] as? Int == 3)
        var forged = proposed; forged["technical_score"] = 100
        let forgedText = try? TIAPreparerPackage.encoded(forged)
        check("E4C1B forbids proposed grades", forgedText.flatMap { try? prep.validate($0) } == nil)
        var altered = proposed; altered["question_set_sha256"] = String(repeating: "f", count: 64)
        let alteredText = try? TIAPreparerPackage.encoded(altered)
        check("E4C1B rejects stale question digest", alteredText.flatMap { try? prep.validate($0) } == nil)
        check("E4C1B no code in public status", !String(describing: validated?.safeStatus ?? [:]).contains("SELECT id"))
    }
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
    let folder = FileManager.default.temporaryDirectory.appendingPathComponent("tia-private-export-test-" + UUID().uuidString)
    do {
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        defer { try? FileManager.default.removeItem(at: folder) }
        let destination = folder.appendingPathComponent("receipt.json")
        let data = Data("{\"synthetic\":true}".utf8)
        try PrivateExport.write(data, to: destination)
        let attrs = try FileManager.default.attributesOfItem(atPath: destination.path)
        check("export private before publication", (attrs[.posixPermissions] as? NSNumber)?.intValue == 0o600)
        let written = try Data(contentsOf: destination)
        check("export exact contents", written == data)
        let link = folder.appendingPathComponent("link.json")
        try FileManager.default.createSymbolicLink(at: link, withDestinationURL: destination)
        do { try PrivateExport.write(Data("unexpected".utf8), to: link); check("export refuses symlink", false) }
        catch { check("export refuses symlink", true) }
        let preserved = try Data(contentsOf: destination)
        check("export symlink target unchanged", preserved == data)
    } catch { check("private export fixture", false) }
    print("Native tests: \(checks - failures) passed, \(failures) failed; provider requests: 0")
    return failures == 0 ? 0 : 1
}
