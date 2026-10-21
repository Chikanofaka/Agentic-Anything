"""Bounded, offline setup contracts. Structure review is never execution proof."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re


CONFIG_VERSION = "tia-interview-config/v1"
SOURCE = "owner:TIA-MASTER-ENGINEERING-DIRECTIVE-v0.3#3"
ENVIRONMENTS = ("POSTGRESQL", "PANDAS")
MECHANISMS = ("STRICT_CHALLENGING", "PROFESSIONAL_SUPPORTIVE")
SOURCES = ("BYOQ", "RANDOM_GENERATED")
MAX_IMPORT_BYTES = 32768
MAX_FIELD_BYTES = 8192


class SetupError(ValueError):
    """Sanitized setup failure; never includes pasted content."""


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class InterviewConfig:
    technical_environment: str
    duration_minutes: int
    difficulty: str
    question_source: str
    interviewer_mechanism: str

    def __post_init__(self) -> None:
        if (self.technical_environment not in ENVIRONMENTS or
                type(self.duration_minutes) is not int or self.duration_minutes not in (45, 60) or
                self.difficulty != "HARD" or self.question_source not in SOURCES or
                self.interviewer_mechanism not in MECHANISMS):
            raise SetupError("UNSUPPORTED_CONFIGURATION")

    @property
    def question_count(self) -> int:
        return 3 if self.duration_minutes == 45 else 4

    def snapshot(self) -> dict:
        value = dict(schema_version=CONFIG_VERSION, source=SOURCE,
                     technical_environment=self.technical_environment,
                     duration_minutes=self.duration_minutes, question_count=self.question_count,
                     difficulty=self.difficulty, question_source=self.question_source,
                     interviewer_mechanism=self.interviewer_mechanism)
        return dict(value, sha256=_digest(value))


def validate_config(value: object) -> InterviewConfig:
    required = {"technical_environment", "duration_minutes", "difficulty",
                "question_source", "interviewer_mechanism"}
    if not isinstance(value, dict) or set(value) - required - {"question_count"} or not required <= set(value):
        raise SetupError("INVALID_CONFIGURATION_FIELDS")
    if any(not isinstance(value[key], str) for key in required - {"duration_minutes"}):
        raise SetupError("INVALID_CONFIGURATION_TYPES")
    config = InterviewConfig(**{key: value[key] for key in required})
    if "question_count" in value and (type(value["question_count"]) is not int or
                                     value["question_count"] != config.question_count):
        raise SetupError("QUESTION_COUNT_CONFLICT")
    return config


_REQUIRED = ("problem_statement", "task", "schema", "example_input", "expected_output", "environment", "source")
_OPTIONAL = ("constraints", "source_reference")
_LABELS = {
    "problem statement": "problem_statement", "task": "task", "schema": "schema",
    "dataframe definitions": "schema", "example input": "example_input",
    "expected output": "expected_output", "environment": "environment",
    "sql dialect": "environment", "source": "source", "constraints": "constraints",
    "source reference": "source_reference",
}


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise SetupError("DUPLICATE_IMPORT_FIELD")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise SetupError("INVALID_IMPORT_ENCODING")


def _parse_labeled(text: str) -> dict:
    fields, current, lines = {}, None, []
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z ]{1,30}):\s*(.*)$", line)
        label = _LABELS.get(match.group(1).lower()) if match else None
        if label:
            if current is not None:
                fields[current] = "\n".join(lines).strip()
            if label in fields or label == current:
                raise SetupError("DUPLICATE_IMPORT_FIELD")
            current, lines = label, [match.group(2)]
        elif current is None:
            if line.strip():
                raise SetupError("LABELED_IMPORT_REQUIRED")
        else:
            lines.append(line)
    if current is not None:
        fields[current] = "\n".join(lines).strip()
    return fields


def _parse_question(value: object) -> dict:
    try:
        if isinstance(value, str):
            if len(value.encode("utf-8")) > MAX_IMPORT_BYTES:
                raise SetupError("IMPORT_TOO_LARGE")
            parsed = json.loads(value, object_pairs_hook=_unique_object,
                                parse_constant=_reject_constant) if value.lstrip().startswith("{") else _parse_labeled(value)
        elif isinstance(value, dict):
            if len(json.dumps(value, allow_nan=False).encode()) > MAX_IMPORT_BYTES:
                raise SetupError("IMPORT_TOO_LARGE")
            parsed = dict(value)
        else:
            raise SetupError("INVALID_IMPORT_TYPE")
    except (TypeError, UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        if isinstance(exc, SetupError):
            raise
        raise SetupError("INVALID_IMPORT_ENCODING") from None
    if not isinstance(parsed, dict) or set(parsed) - set(_REQUIRED + _OPTIONAL):
        raise SetupError("UNKNOWN_IMPORT_FIELDS")
    return parsed


def review_question(value: object, expected_environment: str) -> dict:
    """Parse/review user-owned fields; every executable/semantic claim stays unverified.

    JSON or explicit English headings are accepted. Arbitrary web-page extraction,
    model completion and inferred official hidden tests are intentionally absent.
    The returned fields are editable and must be passed through this function again.
    """
    if expected_environment not in ENVIRONMENTS:
        raise SetupError("UNSUPPORTED_ENVIRONMENT")
    fields = _parse_question(value)
    issues = []
    for key in _REQUIRED:
        if key not in fields or not isinstance(fields[key], str) or not fields[key].strip():
            issues.append({"field": key, "code": "MISSING_OR_INVALID"})
    for key, text in fields.items():
        if not isinstance(text, str):
            issues.append({"field": key, "code": "TEXT_REQUIRED"})
        else:
            try:
                size = len(text.encode("utf-8"))
            except UnicodeError:
                raise SetupError("INVALID_IMPORT_ENCODING") from None
            if size > MAX_FIELD_BYTES:
                issues.append({"field": key, "code": "FIELD_TOO_LARGE"})
            elif "\x00" in text:
                issues.append({"field": key, "code": "INVALID_CONTROL_CHARACTER"})
    environment = fields.get("environment")
    if isinstance(environment, str) and environment.strip().upper() != expected_environment:
        issues.append({"field": "environment", "code": "ENVIRONMENT_CONFLICT"})
    source = fields.get("source")
    if isinstance(source, str) and source.strip().upper() not in ("LEETCODE", "HACKERRANK", "OWNER"):
        issues.append({"field": "source", "code": "SOURCE_REVIEW_REQUIRED"})
    # Detect explicit contradictions; this is not a semantic validator.
    schema = fields.get("schema", "")
    statement = fields.get("problem_statement", "")
    if isinstance(schema, str) and isinstance(statement, str):
        declared = schema + "\n" + statement
        incompatible = r"\b(?:mysql|sqlite|sql server|transact-sql)\b"
        if expected_environment == "POSTGRESQL" and re.search(incompatible, declared, re.I):
            issues.append({"field": "environment", "code": "DIALECT_REVIEW_REQUIRED"})
        if expected_environment == "PANDAS" and re.search(r"\b(?:postgresql|mysql|sqlite)\s+(?:only|required)\b", declared, re.I):
            issues.append({"field": "environment", "code": "DIALECT_REVIEW_REQUIRED"})
    safe_fields = {key: text for key, text in fields.items() if isinstance(text, str)}
    content = {key: safe_fields.get(key) for key in _REQUIRED if key != "source"}
    return {
        "schema_version": "tia-question-review/v1", "fields": safe_fields, "issues": issues,
        "structure_status": "NEEDS_REVIEW" if issues else "STRUCTURALLY_COMPLETE",
        "execution_status": "UNVERIFIED", "grading_authorized": False,
        "semantic_review": "NOT_RUN", "question_id": "byoq-" + _digest(content)[:24],
        "content_sha256": _digest(content),
        "provenance": {
            "kind": "USER_PASTED", "source": safe_fields.get("source", "UNSPECIFIED"),
            "source_reference": safe_fields.get("source_reference", ""),
            "official_hidden_tests": False, "fixtures_validated": False,
            "rule_source": "owner:TIA-MASTER-ENGINEERING-DIRECTIVE-v0.3#5",
        },
    }


def assess_allocation(config: InterviewConfig, reviews: object) -> dict:
    """Revalidate content, not caller-supplied approval flags or question IDs."""
    if not isinstance(config, InterviewConfig) or not isinstance(reviews, list) or len(reviews) > 4:
        raise SetupError("INVALID_QUESTION_ALLOCATION")
    issues, checked = [], []
    if config.question_source == "RANDOM_GENERATED":
        issues.append("APPROVED_GENERATED_POOL_UNAVAILABLE")
    if len(reviews) != config.question_count:
        issues.append("QUESTION_COUNT_MISMATCH")
    for review in reviews:
        if not isinstance(review, dict) or not isinstance(review.get("fields"), dict):
            raise SetupError("INVALID_QUESTION_REVIEW")
        checked.append(review_question(review["fields"], config.technical_environment))
    if any(item["issues"] for item in checked):
        issues.append("QUESTION_REVIEW_REQUIRED")
    if len({item["content_sha256"] for item in checked}) != len(checked):
        issues.append("DUPLICATE_QUESTIONS")
    content_ready = not issues
    return {
        "schema_version": "tia-question-allocation/v1",
        "required_count": config.question_count, "provided_count": len(checked),
        "ready_for_content_review": content_ready, "launch_authorized": False,
        "grading_authorized": False, "issues": issues + ["INDEPENDENT_EXECUTION_VALIDATION_REQUIRED"],
        "question_ids": [item["question_id"] for item in checked],
        "silent_fill_permitted": False,
        "configuration": config.snapshot(),
    }
