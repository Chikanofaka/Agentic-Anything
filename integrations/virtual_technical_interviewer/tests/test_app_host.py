"""Executable native-worker contract tests, using synthetic candidate content."""

import asyncio
import copy
import hashlib
import itertools
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tia_runtime.app_host import HostError, TutorialHost
from tia_runtime.persistence import SaveError, TutorialStore, strict_json


ROOT = Path(__file__).resolve().parents[1]


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class TutorialHostTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.clock = Clock()
        self.host = await TutorialHost.open(self.temporary.name, clock=self.clock)

    async def asyncTearDown(self):
        self.host.close()
        self.temporary.cleanup()

    async def command(self, action, **params):
        result = await self.host.handle({"id": "fixture-request", "action": action, "params": params})
        self.assertTrue(result["ok"], result)
        self.clock.now += 1.25
        return result["state"]

    async def enter_room(self):
        await self.command("tutorial_start")
        for _ in range(3):
            await self.command("tutorial_next")
        self.assertEqual(self.host.state()["screen"], "ROOM")

    async def complete(self):
        await self.enter_room()
        await self.command("tutorial_submit", kind="clarify", text="How should equal timestamps be resolved?")
        await self.command("tutorial_submit", kind="plan", text="I will examine tie and NULL cases.")
        await self.command("tutorial_submit", kind="implement", text="SELECT * FROM Orders;")
        return await self.command("tutorial_complete")

    async def restart(self):
        self.host.close()
        self.host = await TutorialHost.open(self.temporary.name, clock=self.clock)

    async def test_complete_journey_records_input_with_frozen_separate_evidence(self):
        state = await self.complete()
        self.assertEqual(state["screen"], "COMPLETE")
        self.assertEqual(state["tutorial_step"], 5)
        self.assertEqual(state["session"]["phase"], "COMPLETE")
        self.assertEqual(state["execution_status"], "NOT_RUN")
        self.assertEqual(state["api_requests"], 0)
        receipt = state["session"]["receipt"]
        self.assertFalse(receipt["live_model_used"])
        self.assertFalse(receipt["sql_executed"])
        for dimension in ("technical", "communication"):
            self.assertEqual(receipt["assessment"][dimension]["status"], "NOT_SCORED")
            self.assertIsNone(receipt["assessment"][dimension]["value"])
        technical = receipt["assessment"]["technical"]["evidence_ids"]
        communication = receipt["assessment"]["communication"]["evidence_ids"]
        self.assertTrue(set(technical) < set(communication))
        events = state["session"]["events"]
        self.assertEqual([e["kind"] for e in events[-4:]],
                         ["session_closed", "receipt_reviewed", "drill_assigned", "training_completed"])
        self.assertEqual(events[-2]["payload"]["receipt_sha256"], receipt["sha256"])
        self.assertTrue(state["trainer_preview"]["evidence_ids"])
        self.assertIn("sensor", state["trainer_preview"]["follow_up"])
        self.assertEqual(state["trainer_preview"]["provenance"], "SIMULATED")

    async def test_progress_back_next_and_skip_are_host_owned(self):
        await self.command("tutorial_start")
        self.assertEqual(self.host.state()["tutorial_step"], 1)
        await self.command("tutorial_next")
        self.assertEqual(self.host.state()["tutorial_step"], 2)
        await self.command("tutorial_back")
        self.assertEqual(self.host.state()["screen"], "WELCOME")
        await self.command("choose_real")
        self.assertEqual(self.host.state()["screen"], "API_PORTAL")
        self.assertEqual(self.host.state()["model_state"], "offline")
        await self.command("tutorial_back")
        self.assertEqual(self.host.state()["screen"], "ENTRY")

    async def test_back_from_room_does_not_restart_session_or_discard_input(self):
        await self.enter_room()
        await self.command("tutorial_submit", kind="plan", text="Keep this synthetic plan.")
        original = self.host.state()["session"]
        await self.command("tutorial_back")
        await self.command("tutorial_next")
        self.assertEqual(self.host.state()["session"], original)

    async def test_cannot_skip_steps_or_complete_without_candidate_input(self):
        for action in ("tutorial_next", "tutorial_complete"):
            before = self.host.state()
            result = await self.host.handle({"id": "early", "action": action, "params": {}})
            self.assertFalse(result["ok"])
            self.assertEqual(self.host.state(), before)
        await self.enter_room()
        result = await self.host.handle({"id": "empty", "action": "tutorial_complete", "params": {}})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "INPUT_REQUIRED")
        self.assertIsNone(self.host.state()["session"]["receipt"])

    async def test_recovery_preserves_input_progress_and_receipt_exactly(self):
        await self.enter_room()
        await self.command("tutorial_submit", kind="plan", text="Saved synthetic clarification in 中文.")
        before = self.host.state()
        await self.restart()
        self.assertEqual(self.host.state(), before)
        await self.command("tutorial_complete")
        frozen = copy.deepcopy(self.host.state())
        await self.restart()
        self.assertEqual(self.host.state(), frozen)
        receipt = frozen["session"]["receipt"]
        expected = receipt.pop("sha256")
        actual = hashlib.sha256(
            json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        ).hexdigest()
        self.assertEqual(actual, expected)

    async def test_export_contains_actual_code_and_immutable_reviewed_receipt(self):
        await self.complete()
        response = await self.host.handle({"id": "export-test", "action": "export", "params": {}})
        exported = response["export"]
        self.assertIn("SELECT * FROM Orders;", json.dumps(exported))
        self.assertEqual(exported["session"]["receipt"], response["state"]["session"]["receipt"])
        self.assertEqual(exported["api_requests"], 0)
        exported["session"]["receipt"].clear()
        self.assertTrue(self.host.state()["session"]["receipt"])

    async def test_replay_makes_new_session_and_reset_deletes_saved_input(self):
        await self.complete()
        old_id = self.host.state()["session"]["session_id"]
        await self.command("tutorial_replay")
        self.assertIsNone(self.host.state()["session"])
        self.assertEqual(self.host.state()["screen"], "WELCOME")
        for _ in range(3):
            await self.command("tutorial_next")
        self.assertNotEqual(self.host.state()["session"]["session_id"], old_id)
        await self.command("reset")
        self.assertFalse((Path(self.temporary.name) / TutorialStore.filename).exists())
        self.assertFalse(self.host.state()["saved_locally"])
        self.assertIsNone(self.host.state()["session"])
        await self.restart()
        self.assertEqual(self.host.state()["screen"], "ENTRY")
        self.assertIsNone(self.host.state()["session"])

    async def test_corrupt_save_blocks_mutation_and_is_not_overwritten_before_reset(self):
        await self.command("tutorial_start")
        path = Path(self.temporary.name) / TutorialStore.filename
        corrupt = b'{"schema":"broken","private_fixture":"do not overwrite"}'
        path.write_bytes(corrupt)
        await self.restart()
        self.assertEqual(self.host.state()["recovery_error"], "INVALID_SAVE")
        response = await self.host.handle({"id": "blocked", "action": "tutorial_start", "params": {}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "RECOVERY_REQUIRED")
        self.assertEqual(path.read_bytes(), corrupt)
        await self.command("reset")
        self.assertIsNone(self.host.state()["recovery_error"])
        await self.command("tutorial_start")

    async def test_digest_and_future_schema_corruption_fail_closed(self):
        await self.command("tutorial_start")
        path = Path(self.temporary.name) / TutorialStore.filename
        original = path.read_bytes()
        for mutation in ("digest", "schema"):
            document = json.loads(original)
            if mutation == "digest":
                document["state_sha256"] = "0" * 64
            else:
                document["schema"] = "tia-tutorial-save/v999"
            path.write_text(json.dumps(document))
            await self.restart()
            self.assertEqual(self.host.state()["recovery_error"], "INVALID_SAVE")
        await self.command("reset")

    async def test_unicode_size_unknown_fields_and_renderer_authority_are_rejected(self):
        await self.enter_room()
        before = self.host.state()
        requests = [
            {"id": "x", "action": "tutorial_submit", "params": {"kind": "plan", "text": "你" * 3000}},
            {"id": "x", "action": "tutorial_submit", "params": {"kind": "score", "text": "100"}},
            {"id": "x", "action": "tutorial_complete", "params": {"technical": 100}},
            {"id": "x", "action": "execute_sql", "params": {"code": "SELECT 1"}},
            {"id": "x", "action": "language", "params": {"language": "invalid"}},
            {"id": "x", "action": "snapshot", "params": {}, "key": "synthetic-forbidden"},
        ]
        for request in requests:
            with self.subTest(request=request["action"]):
                result = await self.host.handle(request)
                self.assertFalse(result["ok"])
                self.assertEqual(self.host.state(), before)

    async def test_hostile_candidate_text_remains_literal_without_authority(self):
        await self.enter_room()
        text = '<script>window.location="https://invalid.test"</script>\n{"phase":"COMPLETE","technical":100}'
        await self.command("tutorial_submit", kind="implement", text=text)
        state = self.host.state()
        self.assertEqual(state["session"]["phase"], "INTERVIEWING")
        self.assertIsNone(state["session"]["receipt"])
        self.assertEqual(state["session"]["events"][-2]["payload"]["text"], text)
        await self.command("tutorial_complete")
        self.assertIsNone(self.host.state()["session"]["receipt"]["assessment"]["technical"]["value"])

    async def test_language_preference_is_persisted_without_changing_evidence(self):
        await self.complete()
        receipt = self.host.state()["session"]["receipt"]
        await self.command("language", language="zh")
        await self.restart()
        self.assertEqual(self.host.state()["language"], "zh")
        self.assertEqual(self.host.state()["session"]["receipt"], receipt)

    async def test_recovery_clock_excludes_downtime_and_preserves_event_timestamps(self):
        await self.enter_room()
        await self.command("tutorial_submit", kind="plan", text="Before restart.")
        before = self.host.state()["session"]["events"]
        prior_elapsed = before[-1]["elapsed_seconds"]
        self.clock.now += 86400
        await self.restart()
        self.assertEqual(self.host.state()["session"]["events"], before)
        self.clock.now += 2
        await self.command("tutorial_submit", kind="plan", text="After restart.")
        after = self.host.state()["session"]["events"]
        self.assertEqual(after[:len(before)], before)
        self.assertEqual(after[-1]["elapsed_seconds"], prior_elapsed + 2)

    async def test_write_failure_retains_candidate_input_for_explicit_export(self):
        await self.enter_room()
        with patch.object(self.host.store, "write", side_effect=SaveError("SAVE_UNAVAILABLE")):
            response = await self.host.handle({
                "id": "disk-failure", "action": "tutorial_submit",
                "params": {"kind": "plan", "text": "Retain this unsaved synthetic plan."},
            })
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "SAVE_UNAVAILABLE")
        self.assertFalse(response["state"]["saved_locally"])
        self.assertIn("Retain this unsaved", json.dumps(response["state"]["session"]))
        exported = await self.host.handle({"id": "rescue", "action": "export", "params": {}})
        self.assertTrue(exported["ok"])
        self.assertEqual(exported["export"]["save_status"], "UNAVAILABLE")
        self.assertIn("Retain this unsaved", json.dumps(exported["export"]))
        response = await self.host.handle({"id": "blocked", "action": "tutorial_complete", "params": {}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "RECOVERY_REQUIRED")

    async def test_save_has_private_permissions_and_exclusive_writer(self):
        await self.command("tutorial_start")
        path = Path(self.temporary.name) / TutorialStore.filename
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        with self.assertRaises(SaveError) as caught:
            TutorialStore(self.temporary.name)
        self.assertEqual(caught.exception.code, "SAVE_IN_USE")

    async def test_symbolic_link_save_is_rejected_and_reset_never_deletes_target(self):
        await self.command("tutorial_start")
        path = Path(self.temporary.name) / TutorialStore.filename
        target = Path(self.temporary.name) / "target-fixture.txt"
        target.write_text("Preserve this synthetic target.")
        path.unlink()
        path.symlink_to(target)
        await self.restart()
        self.assertEqual(self.host.state()["recovery_error"], "INVALID_SAVE")
        await self.command("reset")
        self.assertEqual(target.read_text(), "Preserve this synthetic target.")

    async def test_reset_removes_crash_staging_files_but_preserves_other_files(self):
        await self.command("tutorial_start")
        directory = Path(self.temporary.name)
        orphan = directory / (".tutorial-" + "a" * 32 + ".tmp")
        orphan.write_text("Synthetic partial-write candidate text")
        unrelated = directory / "preserved.txt"
        unrelated.write_text("Unrelated synthetic fixture")
        await self.command("reset")
        self.assertFalse(orphan.exists())
        self.assertTrue(unrelated.exists())
        self.assertFalse((directory / TutorialStore.filename).exists())

    async def test_action_limit_preserves_room_for_completion(self):
        await self.enter_room()
        for index in range(48):
            await self.command("tutorial_submit", kind="plan", text="Synthetic action {}".format(index))
        response = await self.host.handle(
            {"id": "limit", "action": "tutorial_submit", "params": {"kind": "plan", "text": "Too many"}}
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "ACTION_LIMIT")
        await self.command("tutorial_complete")
        self.assertEqual(self.host.state()["session"]["phase"], "COMPLETE")

    @staticmethod
    def setup_config(environment="POSTGRESQL", duration=45, source="BYOQ",
                     mechanism="STRICT_CHALLENGING"):
        return {
            "technical_environment": environment, "duration_minutes": duration,
            "difficulty": "HARD", "question_source": source,
            "interviewer_mechanism": mechanism,
        }

    @staticmethod
    def setup_question(index=0, environment="POSTGRESQL"):
        return json.dumps({
            "problem_statement": "Synthetic customer case {}".format(index),
            "task": "Return one item per customer.",
            "schema": "orders(order_id integer, customer_id integer)",
            "example_input": "[(1, 1)]", "expected_output": "[(1,)]",
            "environment": environment, "source": "OWNER",
        })

    async def enter_setup(self, config=None):
        await self.command("choose_real")
        await self.command("setup_continue")
        await self.command("setup_config", config=config or self.setup_config())

    async def test_source_selection_changes_from_question_step_and_keeps_launch_blocked(self):
        await self.enter_setup()
        state = await self.command("setup_config", config=self.setup_config(source="RANDOM_GENERATED"))
        self.assertEqual(state["screen"], "QUESTION_SOURCE")
        self.assertEqual(state["setup_config"]["question_source"], "RANDOM_GENERATED")
        self.assertIn("APPROVED_GENERATED_POOL_UNAVAILABLE", state["setup_allocation"]["issues"])
        await self.command("setup_questions", questions=[])
        await self.command("setup_back")
        state = await self.command("setup_config", config=self.setup_config())
        self.assertEqual(state["setup_config"]["question_source"], "BYOQ")
        self.assertFalse(state["setup_allocation"]["launch_authorized"])

    async def test_setup_all_sixteen_combinations_keep_derived_count_and_block_live_launch(self):
        digests = set()
        for environment, duration, source, mechanism in itertools.product(
                ("POSTGRESQL", "PANDAS"), (45, 60), ("BYOQ", "RANDOM_GENERATED"),
                ("STRICT_CHALLENGING", "PROFESSIONAL_SUPPORTIVE")):
            await self.command("reset")
            config = self.setup_config(environment, duration, source, mechanism)
            await self.enter_setup(config)
            count = {45: 3, 60: 4}[duration]
            self.assertEqual(self.host.state()["setup_config"]["question_count"], count)
            questions = ([self.setup_question(index, environment) for index in range(count)]
                         if source == "BYOQ" else [])
            await self.command("setup_questions", questions=questions)
            state = await self.command("setup_mechanism", mechanism=mechanism)
            self.assertEqual(state["screen"], "REVIEW")
            self.assertEqual(state["setup_config"]["status"], "DRAFT")
            self.assertIsNone(state["session"])
            self.assertEqual(state["model_state"], "offline")
            self.assertEqual(state["api_requests"], 0)
            self.assertIn("PROVIDER_AUTHENTICATION_REQUIRED", state["setup_blockers"])
            self.assertIn("INDEPENDENT_EXECUTION_VALIDATION_REQUIRED", state["setup_blockers"])
            self.assertFalse(state["setup_allocation"]["launch_authorized"])
            self.assertEqual(state["setup_profiles"]["interviewer"]["mechanism"], mechanism)
            digests.add(state["setup_config"]["sha256"])
            blocked = await self.host.handle({"id": "blocked-live", "action": "setup_launch", "params": {}})
            self.assertFalse(blocked["ok"])
            self.assertEqual(blocked["error"], "LAUNCH_BLOCKED")
            self.assertEqual(self.host.state(), state)
        self.assertEqual(len(digests), 16)

    async def test_setup_navigation_requires_portal_and_disallows_count_or_authority_fields(self):
        before = self.host.state()
        for action, params in (
                ("setup_continue", {}), ("setup_config", {"config": self.setup_config()}),
                ("setup_questions", {"questions": []}),
                ("setup_mechanism", {"mechanism": "STRICT_CHALLENGING"}),
                ("setup_launch", {})):
            result = await self.host.handle({"id": "too-early", "action": action, "params": params})
            self.assertFalse(result["ok"])
            self.assertEqual(self.host.state(), before)
        await self.command("choose_real")
        await self.command("setup_continue")
        for changes in ({"question_count": 3}, {"difficulty": "EASY"}, {"duration_minutes": True},
                        {"credential": "synthetic-forbidden"}, {"duration_minutes": 30}):
            config = self.setup_config()
            config.update(changes)
            response = await self.host.handle({"id": "invalid-config", "action": "setup_config",
                                               "params": {"config": config}})
            self.assertFalse(response["ok"])
            self.assertEqual(self.host.state()["screen"], "CONFIG")
            self.assertIsNone(self.host.state()["setup_config"])
        await self.command("setup_back")
        self.assertEqual(self.host.state()["screen"], "API_PORTAL")

    async def test_incomplete_byoq_persisted_for_editing_and_exact_allocation_enforced(self):
        await self.enter_setup()
        raw = "A problem without schema or input/output examples."
        result = await self.host.handle({"id": "incomplete", "action": "setup_questions",
                                         "params": {"questions": [raw]}})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "QUESTION_REVIEW_REQUIRED")
        state = self.host.state()
        self.assertEqual(state["screen"], "QUESTION_SOURCE")
        self.assertEqual(state["setup_questions"][0]["raw_input"], raw)
        self.assertEqual(state["setup_questions"][0]["fields"], {})
        self.assertIn("QUESTION_COUNT_MISMATCH", state["setup_allocation"]["issues"])
        self.assertFalse(state["setup_allocation"]["silent_fill_permitted"])
        await self.restart()
        self.assertEqual(self.host.state(), state)
        duplicate = self.setup_question()
        result = await self.host.handle({"id": "duplicate", "action": "setup_questions",
                                         "params": {"questions": [duplicate] * 3}})
        self.assertFalse(result["ok"])
        self.assertIn("DUPLICATE_QUESTIONS", result["state"]["setup_allocation"]["issues"])
        await self.command("setup_questions", questions=[self.setup_question(i) for i in range(3)])
        self.assertEqual(self.host.state()["screen"], "MECHANISM")

    async def test_setup_profile_digests_survive_restart_without_exposing_instructions(self):
        await self.enter_setup()
        await self.command("setup_questions", questions=[self.setup_question(i) for i in range(3)])
        await self.command("setup_mechanism", mechanism="PROFESSIONAL_SUPPORTIVE")
        before = self.host.state()
        for profile in before["setup_profiles"].values():
            self.assertNotIn("instructions", profile)
            self.assertTrue(profile["source_sha256"])
            self.assertEqual(len(profile["sha256"]), 64)
            self.assertFalse(profile["evaluation_profile"]["numeric_scoring_enabled"])
        self.assertIn("instructions", self.host._effective_profiles["interviewer"])
        await self.restart()
        self.assertEqual(self.host.state(), before)
        self.assertIn("instructions", self.host._effective_profiles["interviewer"])
        for expected in ("MECHANISM", "QUESTION_SOURCE", "CONFIG", "API_PORTAL"):
            await self.command("setup_back")
            self.assertEqual(self.host.state()["screen"], expected)
        self.assertEqual(self.host.state()["setup_profiles"], before["setup_profiles"])

    async def test_setup_question_bounds_and_credential_injection_fail_without_mutation(self):
        await self.enter_setup()
        before = self.host.state()
        for questions in ([self.setup_question()] * 5, ["界" * 1400], [{}], ["\ud800"]):
            result = await self.host.handle({"id": "bad-import", "action": "setup_questions",
                                             "params": {"questions": questions}})
            self.assertFalse(result["ok"])
            self.assertEqual(self.host.state(), before)
        result = await self.host.handle({"id": "key-injection", "action": "setup_continue",
                                         "params": {"key": "synthetic-key-not-accepted"}})
        self.assertFalse(result["ok"])
        self.assertNotIn("synthetic-key-not-accepted", json.dumps(self.host.state()))

    async def test_tutorial_receipt_unchanged_through_setup_and_export_labels_draft(self):
        await self.complete()
        frozen = self.host.state()["session"]["receipt"]
        await self.enter_setup()
        await self.command("setup_questions", questions=[self.setup_question(i) for i in range(3)])
        await self.command("setup_mechanism", mechanism="STRICT_CHALLENGING")
        self.assertEqual(self.host.state()["session"]["receipt"], frozen)
        response = await self.host.handle({"id": "setup-export", "action": "export", "params": {}})
        self.assertEqual(response["export"]["setup"]["configuration"]["status"], "DRAFT")
        self.assertEqual(response["export"]["session"]["receipt"], frozen)
        self.assertTrue(response["export"]["contains_personal_input"])
        self.assertNotIn("instructions", response["export"]["setup"]["profiles"]["interviewer"])

    async def test_s03a_v1_digest_remains_compatible_with_additive_setup_fields(self):
        await self.complete()
        state = self.host.state()
        original = {key: value for key, value in state.items()
                    if key not in ("saved_locally", "recovery_error",
                                   "setup_config", "setup_questions", "setup_allocation",
                                   "setup_profiles", "setup_blockers")}
        expected = hashlib.sha256(json.dumps(original, sort_keys=True, separators=(",", ":"),
                                             ensure_ascii=True).encode()).hexdigest()
        path = Path(self.temporary.name) / TutorialStore.filename
        self.assertEqual(json.loads(path.read_text())["state_sha256"], expected)
        await self.restart()
        self.assertEqual(self.host.state(), state)


class WorkerProtocolTests(unittest.TestCase):
    def run_worker(self, lines, data_dir):
        return subprocess.run(
            [sys.executable, "-B", "-u", "-m", "tia_runtime.app_host", "--data-dir", str(data_dir)],
            cwd=ROOT, input=lines, text=True, capture_output=True, timeout=15,
            env={"PATH": "/usr/bin:/bin", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_real_subprocess_roundtrip_records_and_recovers_complete_tutorial(self):
        actions = [
            ("snapshot", {}), ("tutorial_start", {}),
            ("tutorial_next", {}), ("tutorial_next", {}), ("tutorial_next", {}),
            ("tutorial_submit", {"kind": "clarify", "text": "Synthetic subprocess clarification"}),
            ("tutorial_submit", {"kind": "implement", "text": "SELECT * FROM Orders;"}),
            ("tutorial_complete", {}), ("export", {}),
        ]
        lines = "".join(json.dumps({"id": "native-" + str(i), "action": action, "params": params}) + "\n"
                        for i, (action, params) in enumerate(actions))
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_worker(lines, directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            replies = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(replies), len(actions))
            self.assertTrue(all(reply["ok"] for reply in replies))
            self.assertEqual(replies[-1]["export"]["session"]["phase"], "COMPLETE")
            restarted = self.run_worker('{"id":"recover","action":"snapshot","params":{}}\n', directory)
            recovered = json.loads(restarted.stdout)
            self.assertEqual(recovered["state"], replies[-1]["state"])

    def test_protocol_rejects_duplicate_json_nan_and_oversized_line(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_worker(
                '{"id":"x","id":"y","action":"snapshot","params":{}}\n'
                '{"id":"n","action":"snapshot","params":{"x":NaN}}\n', directory
            )
            replies = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual([r["error"] for r in replies], ["INVALID_JSON", "INVALID_JSON"])
            oversized = self.run_worker("x" * 32769 + "\n", directory)
            self.assertEqual(oversized.returncode, 2)
            self.assertEqual(json.loads(oversized.stdout)["error"], "REQUEST_TOO_LARGE")


if __name__ == "__main__":
    unittest.main()
