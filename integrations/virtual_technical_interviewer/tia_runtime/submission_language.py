"""E4-B1: read-only, conservative submission-language projections.

No code execution, credential access, scoring or changes to the saved journal.
The output is an indication for human review, never a language certification.
"""
from __future__ import annotations

import hashlib
import re

SQL_START = re.compile(r'(?is)^(?:\s|--[^\n]*(?:\n|$)|/\*.*?\*/)*(?:WITH|SELECT)\b')
PYTHON_START = re.compile(
    r'(?m)^\s*(?:import\s+pandas\b|from\s+pandas\b|'
    r'import\s+numpy\b|from\s+numpy\b|'
    r'def\s+[A-Za-z_]\w*\s*\(|[A-Za-z_]\w*\s*=\s*pd\.)'
)
SUPPORTED = frozenset(('PANDAS', 'POSTGRESQL'))


def classify_source(value):
    if type(value) is not str or not value.strip():
        return 'UNKNOWN'
    # This is a bounded hint, not a parser. Oversized evidence stays unknown.
    if len(value.encode('utf-8', errors='replace')) > 8192:
        return 'UNKNOWN'
    sql = SQL_START.match(value) is not None
    python = PYTHON_START.search(value) is not None
    if sql and python:
        return 'MIXED_REVIEW_REQUIRED'
    if sql:
        return 'SQL_LIKE_UNVERIFIED'
    if python:
        return 'PYTHON_LIKE_UNVERIFIED'
    return 'UNKNOWN'


def review_session(expected, session, question_index):
    """Derive from the last candidate `implement` event, not the AI reply."""
    events = session.get('events', []) if type(session) is dict else []
    if type(events) is not list:
        events = []
    implementations = [e for e in events if type(e) is dict
                       and e.get('actor') == 'candidate' and e.get('kind') == 'implement'
                       and type(e.get('payload')) is dict
                       and type(e['payload'].get('text')) is str]
    last = implementations[-1] if implementations else None
    source = last['payload']['text'] if last else ''
    style = classify_source(source)
    if last is None:
        status = 'NO_SUBMISSION'
    elif ((expected == 'PANDAS' and style == 'SQL_LIKE_UNVERIFIED') or
          (expected == 'POSTGRESQL' and style == 'PYTHON_LIKE_UNVERIFIED')):
        status = 'LANGUAGE_MISMATCH_REVIEW_REQUIRED'
    elif ((expected == 'PANDAS' and style == 'PYTHON_LIKE_UNVERIFIED') or
          (expected == 'POSTGRESQL' and style == 'SQL_LIKE_UNVERIFIED')):
        status = 'CONSISTENT_BY_HEURISTIC_NOT_EXECUTED'
    else:
        status = 'UNKNOWN_REQUIRE_HUMAN_REVIEW'
    return {
        'schema': 'tia-submission-language-review/v1',
        'source': 'HOST_DERIVED_FROM_CANDIDATE_EVENT',
        'question_index': question_index,
        'expected_environment': expected if expected in SUPPORTED else 'UNKNOWN',
        'observed_style': style,
        'status': status,
        'candidate_event_id': last.get('id') if last else None,
        'candidate_text_sha256': hashlib.sha256(source.encode('utf-8')).hexdigest() if last else None,
        'code_execution_performed_by_review': False,
        'correctness_assessed': False,
    }


def project_language_reviews(rehearsal, active_session=None):
    """Projection excluded from Host state digest for old-save compatibility."""
    plan = rehearsal if type(rehearsal) is dict else {}
    questions = plan.get('questions') or []
    results = plan.get('results') or []
    completed = []
    for index, result in enumerate(results):
        if index >= len(questions):
            break
        question = questions[index] if type(questions[index]) is dict else {}
        completed.append(review_session(question.get('environment'), result.get('session'), index))
    active = None
    if plan.get('status') == 'ACTIVE' and active_session is not None:
        index = plan.get('current_index')
        if type(index) is int and 0 <= index < len(questions):
            question = questions[index] if type(questions[index]) is dict else {}
            active = review_session(question.get('environment'), active_session, index)
    return {
        'schema': 'tia-language-review-projection/v1',
        'source': 'HOST_READ_ONLY_NON_AUTHORITATIVE',
        'active': active,
        'completed': completed,
        'code_execution_performed_by_review': False,
        'correctness_assessed': False,
    }
