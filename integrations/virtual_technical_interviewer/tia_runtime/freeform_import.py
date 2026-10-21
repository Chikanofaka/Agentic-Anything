"""Deterministic, bounded LeetCode/HackerRank-style BYOQ text extraction.

Returns a draft for human editing, not executable fixtures or model authority.
Images are explicitly unsupported in this stage. No network activity occurs.
"""
from __future__ import annotations

import hashlib
import re

MAX_RAW_QUESTION_BYTES = 8192
VALID_ENVIRONMENTS = frozenset(("POSTGRESQL", "PANDAS"))
VALID_SOURCES = frozenset(("LEETCODE", "HACKERRANK", "OWNER"))


class ImportIssue(ValueError):
    """Code-only exception: never expose private raw problem text in errors."""


_TITLE = re.compile(r"^\s*(\d{1,5})\.\s+(.{3,160}?)\s*$")
_TABLE = re.compile(r"^\s*Table\s*:\s*([\w .-]{1,80})\s*$", re.I)
_SCHEMA_HEADING = re.compile(r"^(?:SQL|Pandas)\s+Schema\s*:?(?:\s*[›>].*)?$", re.I)
_EXAMPLE = re.compile(r"^Example(?:\s+(\d+))?\s*:\s*$", re.I)
_SECTION = re.compile(r"^(Input|Output|Explanation|Constraints|Description)\s*:\s*(.*)$", re.I)
_DIFFICULTY = re.compile(r"^(Easy|Medium|Hard)\s*$", re.I)
_TASK = re.compile(r"^(?:Write\b|Return\b|Query\b|Find\b|Identify\b|Given\b|For each\b|Calculate\b|Select\b|List\b|Amazon\b|You are\b)", re.I)
_IMAGE = re.compile(r"(?:\[(?:image|screenshot|diagram)[^\]]*\]|!\[[^\]]*\]\([^)]*\)|schema\s+(?:image|picture|diagram)|described\s+as\s+follows\s*:\s*$)", re.I)
_ORACLE = re.compile(r"\b(?:VARCHAR2|NVARCHAR2|ORACLE|NUMBER\s*\()\b", re.I)


def _checked_text(value):
    if type(value) is not str or not value.strip():
        raise ImportIssue("EMPTY_QUESTION")
    if "\x00" in value:
        raise ImportIssue("INVALID_CONTROL_CHARACTER")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        raise ImportIssue("INVALID_UNICODE") from None
    if size > MAX_RAW_QUESTION_BYTES:
        raise ImportIssue("QUESTION_TOO_LARGE")
    return value.replace("\r\n", "\n").replace("\r", "\n")


def extract_freeform(raw, *, environment, source="OWNER"):
    """Produce explicit, editable extraction fields and provenance.

    Detects textual tables and example sections; does NOT infer missing images,
    hidden tests, SQL semantics, correctness, or approved Hard difficulty.
    """
    if environment not in VALID_ENVIRONMENTS:
        raise ImportIssue("UNSUPPORTED_ENVIRONMENT")
    if source not in VALID_SOURCES:
        raise ImportIssue("UNSUPPORTED_SOURCE")
    text = _checked_text(raw)
    sections = {key: [] for key in ("body", "schema", "input", "output", "explanation", "constraints")}
    section = "body"
    title = None
    declared_difficulty = None
    example_number = None
    task = ""
    for original in text.splitlines():
        line = original.strip()
        if not line:
            if sections[section] and sections[section][-1] != "":
                sections[section].append("")
            continue
        if title is None:
            m = _TITLE.match(line)
            if m:
                title = {"id": m.group(1), "text": m.group(2)}
                continue
        if declared_difficulty is None:
            m = _DIFFICULTY.match(line)
            if m:
                declared_difficulty = m.group(1).upper()
                continue
        m = _TABLE.match(line)
        if m:
            section = "schema"
            sections[section].append(original)
            continue
        if _SCHEMA_HEADING.fullmatch(line):
            # Heading, not a schema row; no proof of a table yet.
            section = "schema"
            continue
        m = _EXAMPLE.match(line)
        if m:
            example_number = m.group(1) or "1"
            section = "body"
            continue
        m = _SECTION.match(line)
        if m:
            label, rest = m.group(1).lower(), m.group(2)
            section = {"input": "input", "output": "output", "explanation": "explanation",
                       "constraints": "constraints", "description": "body"}[label]
            if label in ("input", "output"):
                sections[section].append("Example " + (example_number or "1") + ":")
            if rest:
                sections[section].append(rest)
            continue
        # A full sentence after the table definitions is task prose, not an
        # extra column. Retain table metadata preceding the task in schema.
        if section == "schema" and _TASK.match(line) and not line.startswith("|"):
            section = "body"
        if section == "body" and not task and _TASK.match(line):
            task = line
        sections[section].append(original)

    cleaned = {key: "\n".join(lines).strip() for key, lines in sections.items()}
    if not cleaned["body"] and task:
        cleaned["body"] = task
    schema = cleaned["schema"]
    issues = []
    fields = {
        "problem_statement": cleaned["body"],
        "task": task,
        "schema": schema,
        "example_input": cleaned["input"],
        "expected_output": cleaned["output"],
        "environment": environment,
        "source": source,
        "constraints": cleaned["constraints"],
        "source_reference": "",
    }
    for key in ("problem_statement", "task", "schema", "example_input", "expected_output"):
        if not fields[key]:
            issues.append({"field": key, "code": "MISSING_IN_SOURCE"})
    if not schema and _IMAGE.search(text):
        issues.append({"field": "schema", "code": "IMAGE_SCHEMA_NOT_IMPORTED"})
    if declared_difficulty is None:
        issues.append({"field": "difficulty", "code": "SOURCE_DIFFICULTY_UNKNOWN"})
    elif declared_difficulty != "HARD":
        issues.append({"field": "difficulty", "code": "SOURCE_DIFFICULTY_NOT_HARD"})
    if environment == "POSTGRESQL" and _ORACLE.search(schema):
        issues.append({"field": "environment", "code": "ORACLE_TO_POSTGRESQL_REVIEW"})
    return {
        "schema_version": "tia-freeform-extraction-draft/v1",
        "fields": fields,
        "issues": issues,
        "metadata": {
            "title": title, "declared_difficulty": declared_difficulty,
            "raw_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "raw_utf8_bytes": len(text.encode("utf-8")),
            "explanation_present": bool(cleaned["explanation"]),
            "extraction_method": "DETERMINISTIC_TEXT_RULES",
        },
        "human_confirmed": False,
        "execution_status": "UNVERIFIED",
        "grading_authorized": False,
        "model_called": False,
    }
