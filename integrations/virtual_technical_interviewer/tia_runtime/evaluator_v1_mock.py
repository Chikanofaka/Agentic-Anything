"""E4D-02B: bounded, offline, event-bound Evaluator protocol demonstration.

IMPORTANT: all ratings here are SYNTHETIC DEMONSTRATION values.  This module
performs NO semantic assessment, SQL execution, paid requests or persistence.
A future native-model adapter must submit its own proposals to validate_proposal,
never silently upgrade a mock rating into an actual candidate ability claim.
"""
from __future__ import annotations

import hashlib
import json
import re
from .evaluator_v1_scoring import SCHEMA, WEIGHTS, score_assessment

CLOSED = frozenset(("COMPLETE", "TIMED_OUT", "CLOCK_INTEGRITY_HOLD"))
SUPPORTED_MODES = frozenset(("STRICT_CHALLENGING", "PROFESSIONAL_SUPPORTIVE", "COLLABORATIVE_CONSULTATIVE"))
KIND_RULES = {
    "T2": frozenset(("plan", "implement")),
    "T3": frozenset(("test",)),
    "C1": frozenset(("clarify",)),
    "C2": frozenset(("plan",)),
    "C3": frozenset(("test",)),
}
# Fixed *fictional* anchors test host arithmetic; they are NOT inferred from speech.
DEMO_ANCHORS = {"T2": 3, "T3": 2, "C1": 3, "C2": 2, "C3": 2}
SAFE_ID = re.compile(r"[A-Za-z0-9_.:_-]{1,128}\Z")
CANDIDATE_KINDS = frozenset(("clarify", "plan", "implement", "test", "help"))

class MockContractError(ValueError):
    pass


def _fingerprint(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def packet_from_rehearsal(plan):
    """Derive candidate event references only; never publish raw candidate text."""
    if (type(plan) is not dict or plan.get("status") not in CLOSED or
            type(plan.get("questions")) is not list or len(plan["questions"]) != 3 or
            type(plan.get("results")) is not list or len(plan["results"]) != 3):
        raise MockContractError("EVALUATOR_MOCK_REQUIRES_FROZEN_THREE_QUESTION_RECORD")
    packet = {"schema": "tia-evaluator-v1-event-packet/v1", "questions": [],
              "events": [], "source_digest": _fingerprint({"status": plan["status"],
                                                          "questions": plan["questions"],
                                                          "results": plan["results"]})}
    seen = set()
    for index, result in enumerate(plan["results"]):
        events = result.get("session", {}).get("events") if type(result) is dict and type(result.get("session")) is dict else []
        if type(events) is not list or len(events) > 500:
            raise MockContractError("EVALUATOR_MOCK_INVALID_EVENT_LOG")
        refs = []
        for event in events:
            if type(event) is not dict or event.get("actor") != "candidate" or event.get("kind") not in CANDIDATE_KINDS:
                continue
            identifier = event.get("id")
            if type(identifier) is not str or not SAFE_ID.fullmatch(identifier) or identifier in seen:
                raise MockContractError("EVALUATOR_MOCK_INVALID_EVENT_ID")
            seen.add(identifier)
            if len(refs) >= 100:
                # Do not imply exhaustive event coverage on oversized histories.
                raise MockContractError("EVALUATOR_MOCK_EVENT_LIMIT")
            refs.append(identifier)
            packet["events"].append({"id": identifier, "kind": event["kind"], "question_index": index})
        packet["questions"].append({"question_id": "q"+str(index+1), "candidate_event_ids": refs})
    return packet


def validate_proposal(packet, proposal, source="SYNTHETIC_DEMO"):
    """Validate per-criterion citation membership and source, then use the real 12-metric kernel.

    This function checks structural provenance, not semantic truth or SQL correctness.
    """
    if (type(packet) is not dict or packet.get("schema") != "tia-evaluator-v1-event-packet/v1" or
            type(packet.get("events")) is not list or type(packet.get("questions")) is not list or
            len(packet["questions"]) != 3 or type(proposal) is not dict or
            set(proposal) != {"source_digest", "assessments"} or
            proposal["source_digest"] != packet.get("source_digest") or
            type(proposal["assessments"]) is not list or len(proposal["assessments"]) > 12 or
            source != "SYNTHETIC_DEMO"):
        raise MockContractError("INVALID_MOCK_PROPOSAL")
    index = {e["id"]: e for e in packet["events"]}
    ratings = {id: {"anchor": None, "evidence_event_ids": [], "source": None} for id in WEIGHTS}
    explanations, assigned = {}, set()
    for row in proposal["assessments"]:
        if type(row) is not dict or set(row) != {"metric", "anchor", "citations", "reason"}:
            raise MockContractError("INVALID_MOCK_ROW_FIELDS")
        metric, anchor, citations, reason = row["metric"], row["anchor"], row["citations"], row["reason"]
        if (type(metric) is not str or metric not in KIND_RULES or metric in assigned or
                type(anchor) is not int or not 0 <= anchor <= 4 or
                type(citations) is not list or not 1 <= len(citations) <= 4 or
                any(type(cid) is not str or cid not in index for cid in citations) or
                len(citations) != len(set(citations)) or
                any(index[cid]["kind"] not in KIND_RULES[metric] for cid in citations) or
                type(reason) is not str or not 12 <= len(reason) <= 240):
            raise MockContractError("INVALID_MOCK_RATING_OR_CITATIONS")
        ratings[metric] = {"anchor": anchor, "evidence_event_ids": citations, "source": "SYNTHETIC_DEMO"}
        explanations[metric] = reason
        assigned.add(metric)
    return ratings, explanations


def make_mock_proposal(packet):
    """Deterministic fake model response, referencing only frozen candidate IDs."""
    assignments = []
    for metric, anchor in DEMO_ANCHORS.items():
        matching = [event["id"] for event in packet["events"] if event["kind"] in KIND_RULES[metric]]
        if matching:
            assignments.append({"metric": metric, "anchor": anchor, "citations": matching[:1],
                 "reason": "Synthetic anchor for protocol testing only; no semantic judgment performed."})
    return {"source_digest": packet["source_digest"], "assessments": assignments}


def project_v1_mock(plan, *, mode="STRICT_CHALLENGING"):
    """Read-only integration projection, intentionally *not* an actual Evaluator."""
    if mode not in SUPPORTED_MODES:
        raise MockContractError("INVALID_MOCK_MODE")
    if type(plan) is not dict or plan.get("status") not in CLOSED:
        return {"schema": "tia-evaluator-v1-mock-readout/v1", "status": "IN_PROGRESS"}
    packet = packet_from_rehearsal(plan)
    proposal = make_mock_proposal(packet)
    ratings, explanations = validate_proposal(packet, proposal)
    result = score_assessment({
        "schema": SCHEMA, "interview_id": "mock-" + packet["source_digest"][:20],
        "target_role": "DATA_ANALYST", "seniority": "JUNIOR", "interviewer_mode": mode,
        "questions": packet["questions"], "ratings": ratings,
    })
    result["schema"] = "tia-evaluator-v1-mock-readout/v1"
    result["status"] = "SYNTHETIC_DEMO_ONLY"
    result["mock_rationale"] = explanations
    result["mock_model_calls"] = 0
    result["verified_candidate_score"] = None
    result["source_digest"] = packet["source_digest"]
    result["limitations"].extend([
        "MODEL_RESPONSE_SIMULATED_NOT_ACTUAL_AI_EVALUATION",
        "SYNTHETIC_ANCHORS_DO_NOT_MEASURE_CANDIDATE_COMPETENCE",
        "EVENT_KIND_MATCH_DOES_NOT_ESTABLISH_SEMANTIC_QUALITY",
        "DO_NOT_APPEND_MOCK_SCORE_TO_PERSONAL_PERFORMANCE_HISTORY",
    ])
    return result
