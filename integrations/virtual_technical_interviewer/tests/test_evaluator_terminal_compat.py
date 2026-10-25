"""Regression guard: old terminal rehearsal statuses never crash evaluator projection.

No live provider, SQL runner, personal journal, or persistent save is touched.
"""
import copy
import unittest
from unittest.mock import patch

from tia_runtime import native_evaluator as ne


class TerminalEvaluatorCompatibilityTests(unittest.TestCase):
    def setUp(self):
        # Only the read-only scorecard/profile dependencies are simulated.
        # The actual build_evaluator_report and _card logic runs unmodified.
        self.card = {
            "questions": [
                {"title": f"Question {i+1}", "question_sha256": "a" * 64,
                 "accuracy": {"status": "NOT_VERIFIED", "reason": "NO_APPROVED_LOCAL_FIXTURE",
                              "candidate_event_id": None},
                 "behavior": None, "time": None}
                for i in range(3)
            ]
        }
        technical = {k: 12 for k in ne.IDS[:5]}
        communication = {k: (7 if i < 4 else 6) for i, k in enumerate(ne.IDS[5:])}
        self.profile = {
            "rubric": {"rubric_version": "legacy-test-only", "axes": {
                "technical": {"subscales": technical, "weight_points": 60},
                "communication": {"subscales": communication, "weight_points": 40}}},
            "review_status": "TEST_ONLY", "source_sha256": {}, "prompt_sha256": "b" * 64,
        }

    def _plan(self, status):
        return {"status": status, "questions": [{"content_sha256": "a" * 64} for _ in range(3)],
                "results": [{"outcome": status, "session": {"events": []}} for _ in range(3)]}

    def test_terminal_statuses_are_safe_and_unscored(self):
        for status in ("TIMED_OUT", "CLOCK_INTEGRITY_HOLD"):
            with self.subTest(status=status), \
                 patch.object(ne, "build_scorecard", return_value=copy.deepcopy(self.card)), \
                 patch.object(ne, "compile_evaluator_profile", return_value=self.profile):
                result = ne.build_evaluator_report(self._plan(status))
                self.assertEqual(result["summary"]["overall_grade"], "NOT_SCORED")
                self.assertFalse(result["summary"]["formal_exam_authorized"])
                self.assertEqual(len(result["questions"]), 3)
                self.assertTrue(all(not q["eligible"] for q in result["questions"]))

    def test_complete_still_reads_without_model(self):
        with patch.object(ne, "build_scorecard", return_value=copy.deepcopy(self.card)), \
             patch.object(ne, "compile_evaluator_profile", return_value=self.profile):
            result = ne.build_evaluator_report(self._plan("COMPLETE"))
            self.assertEqual(result["summary"]["overall_grade"], "NOT_SCORED")
            self.assertTrue(all(q["assessment"] is None for q in result["questions"]))

    def test_unknown_status_still_fails_closed(self):
        with self.assertRaises(ne.NativeEvaluatorError) as caught:
            ne._card(self._plan("FORGED_COMPLETE"))
        self.assertEqual(caught.exception.code, "INVALID_EVALUATOR_SOURCE")

    def test_provider_role_widening_is_explicit_and_native_only(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        source = (root / "native" / "OpenAI.swift").read_text(encoding="utf-8")
        self.assertIn('["interviewer", "trainer", "preparer", "evaluator"]', source)
        bridge = (root / "native" / "Bridge.swift").read_text(encoding="utf-8")
        self.assertNotIn('"native_prepare_evaluator"', bridge)
        self.assertNotIn('"native_commit_evaluator"', bridge)


if __name__ == "__main__":
    unittest.main()
