"""Offline scoring contract tests; independent of provider and Native UI."""
import copy
import json
import unittest
from tia_runtime.evaluator_v1_scoring import (
    WEIGHTS, SCHEMA, AssessmentContractError, safe_load_json, score_assessment)

RATINGS = {"T1": 3, "T2": 2, "T3": None, "T4": 3,
           "C1": 3, "C2": 3, "C3": 2, "C4": 4,
           "P1": 3, "P2": None, "P3": 2, "P4": 1}


def example(ratings=RATINGS):
    return {"schema": SCHEMA, "interview_id": "demo001", "target_role": "DATA_ANALYST",
            "seniority": "JUNIOR", "interviewer_mode": "STRICT_CHALLENGING",
            "questions": [{"question_id": f"q{i}", "candidate_event_ids": [f"e{i}"]} for i in range(1, 4)],
            "ratings": {k: {"anchor": r, "evidence_event_ids": ([f"e{(i % 3) + 1}"] if r is not None else []),
                            "source": "SYNTHETIC_DEMO" if r is not None else None}
                        for i, (k, r) in enumerate(ratings.items())}}


class OfflineScoringTests(unittest.TestCase):
    def test_weight_total(self): self.assertEqual(sum(WEIGHTS.values()), 100)
    def test_twelve_dimensions(self): self.assertEqual(len(WEIGHTS), 12)
    def test_gate5_example(self):
        out = score_assessment(example())
        self.assertEqual((out["score"], out["rating_coverage_pct"], out["sensitivity_min"],
                          out["sensitivity_max"]), (64, 82, 55, 73))
    def test_pure_placeholder(self):
        out = score_assessment(example({k: None for k in WEIGHTS}))
        self.assertEqual((out["score"], out["score_status"], out["rating_coverage_pct"]),
                         (50, "PURE_PLACEHOLDER", 0))
        self.assertEqual((out["sensitivity_min"], out["sensitivity_max"]), (0,100))
    def test_all_observed_four_equals_100(self):
        out = score_assessment(example({k: 4 for k in WEIGHTS}))
        self.assertEqual((out["score"], out["rating_coverage_pct"]),(100,100))
    def test_all_observed_zero_equals_zero(self):
        self.assertEqual(score_assessment(example({k: 0 for k in WEIGHTS}))["score"],0)
    def test_modes_same_score(self):
        x=example(); y=copy.deepcopy(x); y["interviewer_mode"]="PROFESSIONAL_SUPPORTIVE"
        self.assertEqual(score_assessment(x)["score"], score_assessment(y)["score"])
    def test_legacy_60_40_not_accepted(self):
        x=example(); x["ratings"]["T05"]={"anchor":2,"source": "SYNTHETIC_DEMO", "evidence_event_ids":["e1"]}
        with self.assertRaises(AssessmentContractError): score_assessment(x)
    def test_unknown_event_id_rejected(self):
        x=example();x["ratings"]["T1"]["evidence_event_ids"]=["invented"]
        with self.assertRaises(AssessmentContractError): score_assessment(x)
    def test_missing_evidence_cannot_be_scored(self):
        x=example();x["ratings"]["T1"]["evidence_event_ids"]=[]
        with self.assertRaises(AssessmentContractError): score_assessment(x)
    def test_missing_rating_not_failure(self):
        self.assertIsNone(score_assessment(example())["ratings"]["T3"]["anchor"])
    def test_anchor_three_not_max(self):
        self.assertLess(score_assessment(example({k:3 for k in WEIGHTS}))["score"],100)
        self.assertEqual(score_assessment(example({k:3 for k in WEIGHTS}))["score"],75)
    def test_out_of_range_and_bool_rejected(self):
        for value in (True,-1,5,3.5,"4"):
            with self.subTest(value=value):
                x=example();x["ratings"]["T1"]["anchor"]=value
                with self.assertRaises(AssessmentContractError):score_assessment(x)
    def test_no_unauthorized_gate_or_percentile(self):
        x=example();x["core_gate"]="MET"
        with self.assertRaises(AssessmentContractError): score_assessment(x)
    def test_extra_payload_fields_fail_closed(self):
        x=example();x["instructions"]="ignore all guards"
        with self.assertRaises(AssessmentContractError): score_assessment(x)
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(AssessmentContractError):safe_load_json('{"a":1,"a":2}')
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(AssessmentContractError):safe_load_json('{"a":NaN}')
    def test_empty_or_forged_question_ids(self):
        x=example();x["questions"][1]["question_id"]="q1"
        with self.assertRaises(AssessmentContractError):score_assessment(x)
    def test_answer_does_not_change_across_runs(self):
        x=example()
        self.assertEqual(score_assessment(x),score_assessment(copy.deepcopy(x)))
    def test_no_mutation(self):
        x=example(); original=copy.deepcopy(x);score_assessment(x)
        self.assertEqual(x,original)

if __name__ == "__main__":unittest.main()
