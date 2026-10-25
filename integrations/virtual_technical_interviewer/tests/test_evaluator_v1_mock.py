"""E4D-02B: isolated event-bound mock protocol, never a semantic AI test."""
import copy
import json
import unittest
from tia_runtime.evaluator_v1_mock import (
    packet_from_rehearsal, make_mock_proposal, validate_proposal,
    project_v1_mock, MockContractError,
)


def synthetic(status="COMPLETE"):
    return {"status": status,
      "questions": [{"title": f"Synthetic Q{i}", "content_sha256": str(i)*64} for i in range(3)],
      "results": [
        {"session":{"events":[
          {"id":"s1-c1", "actor":"candidate", "kind":"clarify", "payload":{"text":"What does first mean?"}},
          {"id":"s1-p1", "actor":"candidate", "kind":"plan", "payload":{"text":"I will separate dates."}},
          {"id":"s1-i1", "actor":"candidate", "kind":"implement", "payload":{"text":"SELECT 1;"}},
          {"id":"s1-t1", "actor":"candidate", "kind":"test", "payload":{"text":"Test duplicate rows."}},
          {"id":"s1-a1", "actor":"interviewer", "kind":"reply", "payload":{"text":"Do you agree?"}},
        ]}},
        {"session":{"events":[{"id":"s2-i1", "actor":"candidate", "kind":"implement", "payload":{"text":"SELECT 2;"}}]}},
        {"session":{"events":[{"id":"s3-i1", "actor":"candidate", "kind":"implement", "payload":{"text":"SELECT 3;"}}]}}]}


class MockContractTests(unittest.TestCase):
    def test_event_bound_mock_returns_nonzero_mock_coverage(self):
        output = project_v1_mock(synthetic())
        self.assertEqual(output["status"], "SYNTHETIC_DEMO_ONLY")
        self.assertGreater(output["rating_coverage_pct"], 0)
        self.assertEqual(output["mock_model_calls"], 0)
        self.assertEqual(output["source_types"], ["SYNTHETIC_DEMO"])
        self.assertIsNone(output["verified_candidate_score"])
        self.assertEqual(output["core_gate"], "UNDETERMINED")
        self.assertEqual(output["industry_percentile"], "BENCHMARK_NOT_AVAILABLE")

    def test_missing_not_zero_and_nonqualifying_metrics(self):
        out = project_v1_mock(synthetic())
        self.assertIsNone(out["ratings"]["T1"]["anchor"])
        self.assertEqual(out["ratings"]["T1"]["status"], "NOT_OBSERVED")
        self.assertTrue(all(out["ratings"][m]["anchor"] is None for m in ("P1","P2","P3","P4")))
        self.assertGreater(out["imputed_points"], 0)

    def test_exact_citations_are_from_original_question(self):
        packet = packet_from_rehearsal(synthetic())
        result = project_v1_mock(synthetic())
        refs = {e["id"] for e in packet["events"]}
        for v in result["ratings"].values():
            self.assertTrue(set(v["evidence_event_ids"]).issubset(refs))

    def test_no_raw_text_or_interviewer_text_in_readout(self):
        val = str(project_v1_mock(synthetic()))
        for word in ["SELECT 1;", "What does first mean?", "Do you agree?"]:
            self.assertNotIn(word, val)

    def test_output_is_deterministic(self):
        self.assertEqual(project_v1_mock(synthetic()), project_v1_mock(synthetic()))

    def test_does_not_mutate_frozen_plan(self):
        value = synthetic(); frozen = copy.deepcopy(value)
        project_v1_mock(value)
        self.assertEqual(value, frozen)

    def test_modes_do_not_reweight_same_evidence(self):
        a = project_v1_mock(synthetic(), mode="STRICT_CHALLENGING")
        b = project_v1_mock(synthetic(), mode="PROFESSIONAL_SUPPORTIVE")
        self.assertEqual((a["score"], a["rating_coverage_pct"]), (b["score"], b["rating_coverage_pct"]))

    def test_active_never_generates_mock_score(self):
        self.assertEqual(project_v1_mock(synthetic("ACTIVE"))["status"], "IN_PROGRESS")

    def test_reject_fake_event_citation(self):
        packet = packet_from_rehearsal(synthetic()); p = make_mock_proposal(packet)
        p["assessments"][0]["citations"] = ["forged-id"]
        with self.assertRaises(MockContractError): validate_proposal(packet, p)

    def test_reject_other_question_wrong_kind(self):
        packet = packet_from_rehearsal(synthetic()); p = make_mock_proposal(packet)
        p["assessments"][0]["citations"] = ["s1-c1"]
        with self.assertRaises(MockContractError): validate_proposal(packet, p)

    def test_reject_stale_digest(self):
        packet = packet_from_rehearsal(synthetic()); p = make_mock_proposal(packet)
        p["source_digest"] = "a"*64
        with self.assertRaises(MockContractError): validate_proposal(packet,p)

    def test_reject_out_of_range_and_boolean_anchor(self):
        packet = packet_from_rehearsal(synthetic())
        for v in (-1, 5, True, 3.5):
            p = make_mock_proposal(packet); p["assessments"][0]["anchor"] = v
            with self.subTest(v=v), self.assertRaises(MockContractError): validate_proposal(packet,p)

    def test_reject_duplicate_metric(self):
        packet = packet_from_rehearsal(synthetic()); p=make_mock_proposal(packet)
        p["assessments"].append(copy.deepcopy(p["assessments"][0]))
        with self.assertRaises(MockContractError): validate_proposal(packet,p)

    def test_reject_unauthorized_technical_correctness(self):
        packet = packet_from_rehearsal(synthetic()); p=make_mock_proposal(packet)
        p["assessments"].append({"metric":"T1","anchor":4,"citations":["s1-i1"],"reason":"Synthetic attempt to claim SQL execution success"})
        with self.assertRaises(MockContractError): validate_proposal(packet,p)

    def test_reject_non_closed_record(self):
        with self.assertRaises(MockContractError): packet_from_rehearsal(synthetic("ACTIVE"))

    def test_reject_cross_question_duplicate_event_id(self):
        plan=synthetic();plan["results"][1]["session"]["events"][0]["id"]="s1-i1"
        with self.assertRaises(MockContractError): packet_from_rehearsal(plan)

    def test_reject_non_list_or_large_event_log(self):
        plan=synthetic();plan["results"][0]["session"]["events"]={}
        with self.assertRaises(MockContractError): packet_from_rehearsal(plan)
        plan=synthetic();plan["results"][0]["session"]["events"]=[{}]*501
        with self.assertRaises(MockContractError): packet_from_rehearsal(plan)

    def test_no_real_model_can_use_mock_source_authority(self):
        packet=packet_from_rehearsal(synthetic());p=make_mock_proposal(packet)
        with self.assertRaises(MockContractError): validate_proposal(packet,p,"MODEL_PROPOSED")

if __name__=="__main__": unittest.main()
