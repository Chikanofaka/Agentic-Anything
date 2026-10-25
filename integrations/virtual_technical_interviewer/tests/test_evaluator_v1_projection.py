"""Synthetic-only acceptance tests for E4D-02A Host-readable 12-metric projection."""
from __future__ import annotations

import copy
import unittest

from tia_runtime.evaluator_v1_projection import project_v1_score


def example(status="COMPLETE"):
    return {"status": status, "questions": [
        {"content_sha256": "a" * 64, "title": "Q1"},
        {"content_sha256": "b" * 64, "title": "Q2"},
        {"content_sha256": "c" * 64, "title": "Q3"}],
        "results": [{"session": {"events": [{"actor": "candidate", "kind": "implement", "id": "q1-e1",
                                             "payload": {"text": "SYNTHETIC_SQL_DO_NOT_EXECUTE"}}]}},
                    {"session": {"events": []}}, {"session": {"events": []}}]}


class V1ProjectionTests(unittest.TestCase):
    def test_closed_has_visible_placeholder(self):
        result = project_v1_score(example())
        self.assertEqual((result["score"], result["score_status"], result["rating_coverage_pct"]),
                         (50, "PURE_PLACEHOLDER", 0))
        self.assertEqual((result["sensitivity_min"], result["sensitivity_max"]), (0, 100))
        self.assertEqual(len(result["metrics"]), 12)
        self.assertEqual(sum(x["max_points"] for x in result["metrics"].values()), 100)

    def test_no_raw_interview_text_in_projection(self):
        self.assertNotIn("SYNTHETIC_SQL_DO_NOT_EXECUTE", str(project_v1_score(example())))

    def test_not_mutating_history(self):
        source = example(); frozen = copy.deepcopy(source)
        project_v1_score(source)
        self.assertEqual(source, frozen)

    def test_deterministic(self):
        self.assertEqual(project_v1_score(example()), project_v1_score(example()))

    def test_interviewer_mode_invariant(self):
        a = project_v1_score(example(), mode="STRICT_CHALLENGING")
        b = project_v1_score(example(), mode="PROFESSIONAL_SUPPORTIVE")
        self.assertEqual((a["score"], a["axes"]), (b["score"], b["axes"]))

    def test_no_ai_or_verified_claim(self):
        result = project_v1_score(example())
        self.assertIsNone(result["verified_score"])
        self.assertEqual(result["core_gate"], "UNDETERMINED")
        self.assertEqual(result["industry_percentile"], "BENCHMARK_NOT_AVAILABLE")
        self.assertFalse(result["legacy_evaluator_proposals_imported"])

    def test_timed_out_can_show_score(self):
        self.assertEqual(project_v1_score(example("TIMED_OUT"))["score_status"], "PURE_PLACEHOLDER")

    def test_active_does_not_assess(self):
        result = project_v1_score(example("ACTIVE"))
        self.assertEqual(result["status"], "IN_PROGRESS")
        self.assertIsNone(result["score"])

    def test_bad_inputs_rejected(self):
        for value in (None, {}, {"status": "COMPLETE", "questions": []}):
            with self.assertRaises(ValueError): project_v1_score(value)

    def test_unknown_role_rejected(self):
        with self.assertRaises(ValueError): project_v1_score(example(), role="CEO")

    def test_synthetic_counts(self):
        self.assertEqual(project_v1_score(example())["candidate_event_counts"], [1, 0, 0])


if __name__ == "__main__":
    unittest.main()
