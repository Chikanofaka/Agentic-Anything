"""TIA E4D Takeover 01 -- offline experimental 12-metric scoring core.

Strictly data-only. Does not import the interview controller, execute SQL, call
an AI provider, or read/write session history. No credential or network access.
Weighting is experimental, not a hiring-grade validated cut score.
"""

from __future__ import annotations

from decimal import Decimal
import json
from typing import Any

SCHEMA = "tia-evaluator-score-input/v1"
RESULT_SCHEMA = "tia-evaluator-score-result/v1"
POLICY_VERSION = "tia-scoring-design/v1.0-experimental"
WEIGHTS = {
    "T1": 25, "T2": 20, "T3": 15, "T4": 10,
    "C1": 6, "C2": 6, "C3": 4, "C4": 4,
    "P1": 3, "P2": 3, "P3": 2, "P4": 2,
}
AXES = {"technical": tuple(k for k in WEIGHTS if k.startswith("T")),
        "communication": tuple(k for k in WEIGHTS if k.startswith("C")),
        "professional_behavior": tuple(k for k in WEIGHTS if k.startswith("P"))}
MODES = {"STRICT_CHALLENGING", "PROFESSIONAL_SUPPORTIVE", "COLLABORATIVE_CONSULTATIVE"}
SOURCES = {"SYNTHETIC_DEMO", "MODEL_PROPOSED", "HUMAN_REVIEWED"}
MISSING_ANCHOR = 2


class AssessmentContractError(ValueError):
    """Malformed input, unsupported grading authority or forged evidence ref."""


def _fields(value: Any, expected: set[str], context: str) -> None:
    if type(value) is not dict or set(value) != expected:
        raise AssessmentContractError(f"INVALID_{context}_FIELDS")


def _safe_id(value: Any) -> bool:
    return type(value) is str and 1 <= len(value) <= 128 and all(
        c.isascii() and (c.isalnum() or c in "_-:.") for c in value
    )


def _number(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def score_assessment(payload: dict[str, Any]) -> dict[str, Any]:
    """Produce an MVM numeric score plus explicit uncertainty and evidence limits.

    All nonmissing ratings are *provisional*, even if human-reviewed. Gate
    authority and actual SQL validation remain outside this offline kernel.
    """
    _fields(payload, {"schema", "interview_id", "target_role", "seniority",
                      "interviewer_mode", "questions", "ratings"}, "TOP_LEVEL")
    if payload["schema"] != SCHEMA or not _safe_id(payload["interview_id"]):
        raise AssessmentContractError("INVALID_INTERVIEW_ID_OR_SCHEMA")
    if type(payload["interviewer_mode"]) is not str or payload["interviewer_mode"] not in MODES:
        raise AssessmentContractError("UNSUPPORTED_INTERVIEWER_MODE")
    if payload["target_role"] not in ("DATA_ANALYST", "DATA_ENGINEER", "FDE"):
        raise AssessmentContractError("UNKNOWN_ROLE")
    if payload["seniority"] not in ("JUNIOR", "MID"):
        raise AssessmentContractError("UNKNOWN_SENIORITY")
    questions = payload["questions"]
    if type(questions) is not list or len(questions) != 3:
        raise AssessmentContractError("THREE_QUESTIONS_REQUIRED")
    evidence_to_question = {}
    question_ids = set()
    for i, question in enumerate(questions):
        _fields(question, {"question_id", "candidate_event_ids"}, "QUESTION")
        qid = question["question_id"]
        if not _safe_id(qid) or qid in question_ids:
            raise AssessmentContractError("INVALID_OR_DUPLICATE_QUESTION_ID")
        question_ids.add(qid)
        events = question["candidate_event_ids"]
        if type(events) is not list or len(events) > 100:
            raise AssessmentContractError("INVALID_EVENT_LIST")
        for event_id in events:
            if not _safe_id(event_id) or event_id in evidence_to_question:
                raise AssessmentContractError("INVALID_OR_DUPLICATE_EVENT_ID")
            evidence_to_question[event_id] = i
    ratings = payload["ratings"]
    if type(ratings) is not dict or set(ratings) != set(WEIGHTS):
        raise AssessmentContractError("RATING_KEYS_MUST_MATCH_TWELVE_METRICS")
    if sum(WEIGHTS.values()) != 100:
        raise AssessmentContractError("INTERNAL_WEIGHT_ERROR")

    details = {}
    observed_contribution = Decimal(0)
    missing_weight = 0
    sources = set()
    for metric, weight in WEIGHTS.items():
        entry = ratings[metric]
        _fields(entry, {"anchor", "evidence_event_ids", "source"}, "RATING")
        anchor, evidence, source = entry["anchor"], entry["evidence_event_ids"], entry["source"]
        if type(evidence) is not list or len(evidence) > 8 or any(not _safe_id(x) for x in evidence):
            raise AssessmentContractError(f"INVALID_EVIDENCE_LIST_{metric}")
        if len(evidence) != len(set(evidence)) or not set(evidence).issubset(evidence_to_question):
            raise AssessmentContractError(f"FORGED_OR_DUPLICATE_EVIDENCE_{metric}")
        if anchor is None:
            if evidence or source is not None:
                raise AssessmentContractError(f"MISSING_RATING_CANNOT_CLAIM_EVIDENCE_{metric}")
            missing_weight += weight
            details[metric] = {"status": "NOT_OBSERVED", "anchor": None,
                               "max_points": weight, "score_contribution": None,
                               "imputed_points": _number(Decimal(weight) / 2),
                               "evidence_event_ids": [], "source": None}
            continue
        if type(anchor) is not int or not 0 <= anchor <= 4:
            raise AssessmentContractError(f"ANCHOR_MUST_BE_INTEGER_0_TO_4_{metric}")
        if not evidence or type(source) is not str or source not in SOURCES:
            raise AssessmentContractError(f"RATING_REQUIRES_VALID_SOURCE_CITATION_{metric}")
        sources.add(source)
        contribution = Decimal(weight) * Decimal(anchor) / Decimal(4)
        observed_contribution += contribution
        details[metric] = {"status": "PROVISIONAL_RATING", "anchor": anchor,
                           "max_points": weight, "score_contribution": _number(contribution),
                           "imputed_points": 0, "evidence_event_ids": list(evidence), "source": source}

    placeholder_contribution = Decimal(missing_weight) * Decimal(MISSING_ANCHOR) / Decimal(4)
    total = observed_contribution + placeholder_contribution
    state = ("PURE_PLACEHOLDER" if missing_weight == 100 else
             "RATED_PROVISIONAL" if missing_weight == 0 else "MIXED_PROVISIONAL_AND_IMPUTED")
    axes = {}
    for axis, keys in AXES.items():
        axis_observed = sum(WEIGHTS[k] for k in keys if details[k]["anchor"] is not None)
        axes[axis] = {"maximum": sum(WEIGHTS[k] for k in keys),
                      "rated_weight": axis_observed,
                      "provisional_points": _number(sum(
                          (Decimal(details[k]["score_contribution"]) if details[k]["anchor"] is not None
                           else Decimal(details[k]["imputed_points"])) for k in keys
                      ))}

    return {"schema": RESULT_SCHEMA, "policy_version": POLICY_VERSION,
            "interview_id": payload["interview_id"], "target_role": payload["target_role"],
            "seniority": payload["seniority"], "interviewer_mode": payload["interviewer_mode"],
            "score": _number(total), "score_status": state,
            "rating_coverage_pct": 100 - missing_weight,
            "verified_sql_coverage": "NOT_ASSESSED_BY_OFFLINE_KERNEL",
            "sensitivity_min": _number(observed_contribution),
            "sensitivity_max": _number(observed_contribution + Decimal(missing_weight)),
            "imputed_points": _number(placeholder_contribution), "axes": axes,
            "ratings": details, "core_gate": "UNDETERMINED",
            "job_readiness": "INSUFFICIENT_EVIDENCE",
            "industry_percentile": "BENCHMARK_NOT_AVAILABLE",
            "human_review_required": True,
            "source_types": sorted(sources),
            "limitations": [
                "EXPERIMENTAL_WEIGHTS_NOT_CALIBRATED",
                "MODEL_PROPOSALS_ARE_NOT_EXECUTION_FACTS",
                "MISSING_RATINGS_IMPUTED_AT_ANCHOR_2_FOR_MVM_ONLY",
                "NO_HIRING_PROBABILITY_OR_INDUSTRY_PERCENTILE",
                "ROLE_AND_ASSISTANCE_CONDITIONS_REQUIRE_FUTURE_CALIBRATION",
            ]}


def safe_load_json(text: str) -> dict[str, Any]:
    """Reject duplicate keys and non-finite values rather than reinterpreting them."""
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise AssessmentContractError("DUPLICATE_JSON_KEY")
            out[key] = value
        return out
    def bad_constant(value):
        raise AssessmentContractError(f"NONFINITE_JSON_VALUE_{value}")
    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=bad_constant)
    except (ValueError, TypeError, RecursionError) as exc:
        raise AssessmentContractError("INVALID_JSON") from exc
    if type(value) is not dict:
        raise AssessmentContractError("TOP_LEVEL_MUST_BE_OBJECT")
    return value
