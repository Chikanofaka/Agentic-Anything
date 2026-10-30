"""E3-A: read-only, source-bound rehearsal observations; never a competency grade.

Build exclusively from already committed rehearsal/SQL/clock records. The model,
renderer and replay path cannot supply subjective scores or execute SQL here.
The checksum detects local drift only; it is not an attested signature.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

SCHEMA = 'tia-evidence-scorecard/v1'
SHA = re.compile(r'[0-9a-f]{64}\Z')
VERIFIED_STATUSES = {'PASSED', 'FAILED', 'EXECUTION_ERROR'}


def _seconds(value):
    return round(value, 6) if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None


def _session_events(result):
    session = result.get('session') or {}
    events = session.get('events', []) if type(session) is dict else []
    return events if type(events) is list else []


def _candidate_metrics(events):
    candidate = [event for event in events if type(event) is dict and event.get('actor') == 'candidate'
                 and event.get('kind') in ('clarify', 'plan', 'implement', 'help', 'test')]
    return {
        'candidate_turns': len(candidate),
        'clarifications': sum(e['kind'] == 'clarify' for e in candidate),
        'help_requests': sum(e['kind'] == 'help' for e in candidate),
        'sql_submissions': sum(e['kind'] == 'implement' for e in candidate),
        'evidence_event_ids': [e['id'] for e in candidate if type(e.get('id')) is str],
    }


def _verified_grade(grade, question_hash, events, *, skipped=False):
    """Return an observation only for the last submitted SQL and a bound receipt.

    A prior SQL PASS followed by a new implement event is not proof of the latest
    code. Unavailable tests and all earlier versions remain explicitly unverified.
    """
    default = {
        'status': 'NOT_VERIFIED', 'reason': 'NO_APPROVED_LOCAL_FIXTURE',
        'fixture_passed': None, 'fixture_total': None,
        'candidate_event_id': None, 'candidate_sql_sha256': None,
        'fixture_sha256': None, 'backend': 'NOT_RUN',
    }
    if not isinstance(grade, dict):
        return default
    details = grade.get('result')
    if (grade.get('correctness') != 'VERIFIED_LOCAL_FIXTURE' or
            not isinstance(details, dict) or details.get('status') not in VERIFIED_STATUSES):
        return dict(default, reason='LOCAL_EXECUTION_NOT_VERIFIED')
    suite = grade.get('schema') == 'tia-post-interview-sql-accuracy/v1'
    total = grade.get('total_approved_fixtures')
    passed = grade.get('passed_fixtures')
    if suite:
        observation = grade.get('post_interview_observation') or {}
        cases = observation.get('cases') or []
        if (type(total) is not int or not 1 <= total <= 6 or type(passed) is not int or not 0 <= passed <= total
                or len(cases) != total or sum(c.get('status') == 'PASSED' for c in cases) != passed
                or any(c.get('status') not in VERIFIED_STATUSES for c in cases)):
            return dict(default, reason='GRADE_EVIDENCE_MISMATCH')
    if (grade.get('source') != 'EPHEMERAL_POSTGRESQL_LOCAL' or
            grade.get('approval_kind') != 'NATIVE_HUMAN_CONFIRMATION' or
            grade.get('official_hidden_tests') is not False or
            grade.get('question_sha256') != question_hash or
            (not suite and (total != 1 or passed not in (0, 1))) or
            (details['status'] == 'PASSED') != (passed == total)):
        return dict(default, reason='GRADE_EVIDENCE_MISMATCH')
    target_id = grade.get('candidate_event_id')
    target_sha = grade.get('candidate_sql_sha256')
    fixture_sha = grade.get('fixture_sha256')
    if (type(target_id) is not str or type(target_sha) is not str or not SHA.fullmatch(target_sha)
            or type(fixture_sha) is not str or not SHA.fullmatch(fixture_sha)):
        return dict(default, reason='GRADE_EVIDENCE_MISMATCH')
    implementations = [e for e in events if type(e) is dict and e.get('actor') == 'candidate'
                       and e.get('kind') == 'implement']
    if not implementations:
        return dict(default, reason='GRADE_SUBMISSION_NOT_FOUND')
    matching = [e for e in implementations if e.get('id') == target_id]
    if len(matching) != 1:
        return dict(default, reason='GRADE_SUBMISSION_NOT_FOUND')
    payload = matching[0].get('payload') or {}
    sql = payload.get('text') if type(payload) is dict else None
    if type(sql) is not str or hashlib.sha256(sql.encode('utf-8')).hexdigest() != target_sha:
        return dict(default, reason='GRADE_SQL_HASH_MISMATCH')
    observation = {
        'status': details['status'], 'reason': 'POST_INTERVIEW_REVIEWED_CASES_ONLY' if suite else 'SINGLE_APPROVED_LOCAL_FIXTURE_ONLY',
        'fixture_passed': grade['passed_fixtures'], 'fixture_total': total,
        'candidate_event_id': target_id, 'candidate_sql_sha256': target_sha,
        'fixture_sha256': fixture_sha, 'backend': 'EPHEMERAL_POSTGRESQL_LOCAL',
    }
    if implementations[-1].get('id') != target_id:
        # Preserve the observed historical result but never count it as final.
        return dict(observation, status='NOT_VERIFIED', reason='TESTED_PRIOR_SQL_VERSION')
    if skipped and not suite:
        return dict(observation, status='NOT_VERIFIED', reason='QUESTION_SKIPPED_AFTER_TEST')
    return observation


def build_scorecard(plan):
    """Deterministic additive view; not persisted as an independent source of truth."""
    if type(plan) is not dict or type(plan.get('questions')) is not list or len(plan['questions']) != 3:
        raise ValueError('INVALID_REHEARSAL_SCORECARD_SOURCE')
    questions = plan['questions']
    results = plan.get('results') or []
    if type(results) is not list or len(results) > 3:
        raise ValueError('INVALID_REHEARSAL_SCORECARD_SOURCE')
    output = []
    verified = passed = failed = execution_errors = 0
    totals = dict(candidate_turns=0, clarifications=0, help_requests=0, sql_submissions=0)
    for i, q in enumerate(questions):
        record = results[i] if i < len(results) else None
        session_events = _session_events(record) if isinstance(record, dict) else []
        metrics = _candidate_metrics(session_events) if record is not None else None
        if metrics:
            for k in totals:
                totals[k] += metrics[k]
        qsha = q.get('content_sha256')
        grade = (record.get('sql_accuracy') if isinstance(record, dict) else None)
        skipped = isinstance(record, dict) and record.get('outcome') in ('SKIPPED', 'NOT_REACHED')
        accuracy = (_verified_grade(grade, qsha, session_events, skipped=skipped)
                    if isinstance(record, dict) else
                    {'status': 'NOT_VERIFIED', 'reason': 'QUESTION_NOT_CLOSED',
                     'fixture_passed': None, 'fixture_total': None, 'candidate_event_id': None,
                     'candidate_sql_sha256': None, 'fixture_sha256': None, 'backend': 'NOT_RUN'})
        if accuracy['status'] in VERIFIED_STATUSES:
            verified += 1
            passed += int(accuracy['status'] == 'PASSED')
            failed += int(accuracy['status'] == 'FAILED')
            execution_errors += int(accuracy['status'] == 'EXECUTION_ERROR')
        time_metrics = record.get('time_metrics') if isinstance(record, dict) else None
        detail = {
            'index': i, 'title': q.get('title') or 'Question', 'question_sha256': qsha,
            'state': ('CLOSED' if record is not None else
                      'ACTIVE_NOT_CLOSED' if plan.get('status') == 'ACTIVE'
                      and plan.get('current_index') == i else 'NOT_REACHED'),
            'outcome': record.get('outcome') if isinstance(record, dict) else None,
            'accuracy': accuracy, 'behavior': metrics,
            'time': ({'elapsed_seconds': _seconds(time_metrics.get('elapsed_seconds')),
                      'model_wait_seconds': _seconds(time_metrics.get('model_wait_seconds'))}
                     if type(time_metrics) is dict else None),
            'session_receipt_sha256': ((record.get('session') or {}).get('receipt') or {}).get('sha256')
                if isinstance(record, dict) else None,
        }
        output.append(detail)
    timing = plan.get('timing') or {}
    card = {
        'schema': SCHEMA, 'status': ('FINAL' if plan.get('status') != 'ACTIVE' else 'IN_PROGRESS'),
        'rehearsal_status': plan.get('status'), 'source': 'DERIVED_FROM_REHEARSAL_JOURNAL',
        'questions': output,
        'summary': {
            'total_questions': 3, 'closed_questions': len(results),
            'latest_sql_locally_verified_questions': verified,
            'latest_sql_passed_local_fixtures': passed,
            'latest_sql_failed_local_fixtures': failed,
            'latest_sql_execution_errors': execution_errors,
            'questions_without_current_sql_verification': 3 - verified,
            'observed_closed_question_actions': totals,
            'elapsed_seconds': _seconds(timing.get('elapsed_seconds')),
            'model_wait_seconds': _seconds(timing.get('model_wait_seconds')),
            'time_integrity': timing.get('integrity') or 'NOT_AVAILABLE',
            'clock_certified': False,
            'technical_capability': 'NOT_SCORED',
            'communication_competency': 'NOT_SCORED',
            'overall_grade': 'NOT_SCORED', 'formal_exam_authorized': False,
        },
        'limitations': [
            'Local, human-reviewed fixtures only; no official hidden tests.',
            'Fixture counts are evidence coverage, not competency percentages.',
            'Behavior counts show actions, not communication quality.',
            'Local clock is untrusted for certification; trainer and weighted grades are not provided.',
        ],
    }
    card['sha256'] = hashlib.sha256(json.dumps(card, sort_keys=True, ensure_ascii=True,
                                             separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return card
