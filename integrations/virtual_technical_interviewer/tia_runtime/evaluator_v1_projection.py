"""Read-only E4D v1.0 MVM score projection from a frozen three-question interview.

This additive bridge intentionally does NOT translate uncalibrated historical 60/40
AI proposals into the approved 12-dimensional experimental rubric. Before an
independent v1.0 assessor is installed, every rating remains NOT_OBSERVED.
The resulting 50/100 is a visibly PURE_PLACEHOLDER UI demonstration, not an
ability estimate. Source facts are never edited, and no persistence occurs here.
"""

from __future__ import annotations

import hashlib
import json

from .evaluator_v1_scoring import SCHEMA, WEIGHTS, score_assessment

CLOSED = frozenset(("COMPLETE", "TIMED_OUT", "CLOCK_INTEGRITY_HOLD"))
_ALLOWED_ROLES = {"DATA_ANALYST", "DATA_ENGINEER", "FDE"}
_ALLOWED_LEVELS = {"JUNIOR", "MID"}
_ALLOWED_MODES = {"STRICT_CHALLENGING", "PROFESSIONAL_SUPPORTIVE", "COLLABORATIVE_CONSULTATIVE"}


def _fingerprint(value):
    try:
        canonical = json.dumps(value, ensure_ascii=True, sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError, RecursionError) as exc:
        raise ValueError("EVALUATOR_V1_INVALID_REHEARSAL") from exc
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _candidate_counts(plan):
    """No raw SQL, text, or identity is exported in this read-only projection."""
    counts = []
    for idx in range(3):
        results = plan.get("results", [])
        result = results[idx] if type(results) is list and idx < len(results) else None
        session = result.get("session") if type(result) is dict else None
        events = session.get("events") if type(session) is dict else None
        if type(events) is not list:
            counts.append(0)
            continue
        counts.append(sum(type(event) is dict and event.get("actor") == "candidate"
                          for event in events))
    return counts


def project_v1_score(plan, *, mode="STRICT_CHALLENGING", role="DATA_ANALYST", seniority="JUNIOR"):
    """Return a standalone scorecard for a CLOSED interview; never grant grade authority.

    A later E4D module can supply schema-validated 12-metric ratings to the
    deterministic kernel. This slice deliberately does not infer them.
    """
    if type(plan) is not dict or type(plan.get("questions")) is not list or len(plan["questions"]) != 3:
        raise ValueError("EVALUATOR_V1_THREE_QUESTIONS_REQUIRED")
    if type(plan.get("status")) is not str:
        raise ValueError("EVALUATOR_V1_INVALID_STATUS")
    if mode not in _ALLOWED_MODES or role not in _ALLOWED_ROLES or seniority not in _ALLOWED_LEVELS:
        raise ValueError("EVALUATOR_V1_INVALID_CONFIGURATION")

    is_closed = plan["status"] in CLOSED
    if not is_closed:
        return {"schema": "tia-evaluator-v1-mvm-readout/v1", "status": "IN_PROGRESS",
                "policy_version": "tia-scoring-design/v1.0-experimental",
                "score": None, "score_status": "NOT_YET_CALCULATED",
                "limitations": ["SCORE_ONLY_AFTER_CLOSURE"]}

    digest = _fingerprint({"questions": plan["questions"],
                          "results": plan.get("results"), "status": plan["status"]})
    payload = {
        "schema": SCHEMA, "interview_id": "mvm-" + digest[:20],
        "target_role": role, "seniority": seniority, "interviewer_mode": mode,
        "questions": [{"question_id": "q" + str(i + 1), "candidate_event_ids": []}
                      for i in range(3)],
        "ratings": {metric: {"anchor": None, "evidence_event_ids": [], "source": None}
                    for metric in WEIGHTS},
    }
    scored = score_assessment(payload)
    return {
        "schema": "tia-evaluator-v1-mvm-readout/v1", "status": "DEMO_READY",
        "score": scored["score"], "score_status": scored["score_status"],
        "rating_coverage_pct": scored["rating_coverage_pct"],
        "sensitivity_min": scored["sensitivity_min"], "sensitivity_max": scored["sensitivity_max"],
        "imputed_points": scored["imputed_points"], "axes": scored["axes"],
        "metrics": scored["ratings"], "core_gate": scored["core_gate"],
        "job_readiness": scored["job_readiness"],
        "industry_percentile": scored["industry_percentile"],
        "policy_version": scored["policy_version"],
        "provisional_interview_id": scored["interview_id"],
        "candidate_event_counts": _candidate_counts(plan),
        "legacy_evaluator_proposals_imported": False,
        "verified_score": None,
        "limitations": [
            "PURE_PLACEHOLDER_IS_NOT_CANDIDATE_SCORE",
            "LEGACY_60_40_PROPOSALS_NOT_MAPPED_TO_V1",
            "NO_AI_SEMANTIC_EVALUATION_OR_SQL_EXECUTION_IN_THIS_SLICE",
            "NO_INDUSTRY_PERCENTILE_OR_HIRING_PREDICTION",
            "NO_HISTORY_APPEND_OR_DISK_MUTATION",
        ],
    }
