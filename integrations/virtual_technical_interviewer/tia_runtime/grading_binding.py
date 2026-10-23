"""E2.5-B: exact current-question, candidate-code, approved-fixture binding.

This module never executes SQL. A human review and native OS confirmation
precede the separate ephemeral local PostgreSQL runner. Saved observations
are checked against their original, locally journalled inputs on recovery.
"""
from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
import re

from .sql_accuracy import AccuracyError, validate_fixture

SHA = re.compile(r'[0-9a-f]{64}\Z')
MAX_UI_FIXTURE_BYTES = 12000
# Fixed, machine-local locations only. Renderer cannot nominate a binary or DSN.
APPROVED_PG_CONFIG = (
    '/opt/anaconda3/bin/pg_config',
    '/opt/homebrew/opt/postgresql@17/bin/pg_config',
    '/opt/homebrew/bin/pg_config',
    '/usr/local/opt/postgresql@17/bin/pg_config',
    '/usr/local/bin/pg_config',
    '/usr/bin/pg_config',
)


class GradingBindingError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def inspect_binding(fixture_json, question_sha256, event_id, sql_sha256, question_index):
    if type(fixture_json) is not str or not 0 < len(fixture_json.encode('utf-8')) <= MAX_UI_FIXTURE_BYTES:
        raise GradingBindingError('INVALID_GRADE_FIXTURE_SIZE')
    if type(question_sha256) is not str or SHA.fullmatch(question_sha256) is None:
        raise GradingBindingError('INVALID_CURRENT_QUESTION')
    try:
        fixture, fixture_sha256 = validate_fixture(fixture_json.encode('utf-8'))
    except AccuracyError as exc:
        raise GradingBindingError(exc.code) from None
    if fixture['question_sha256'] != question_sha256:
        raise GradingBindingError('FIXTURE_QUESTION_MISMATCH')
    # A fixture's expected output is an owner-reviewed target; it is never
    # sent to the AI interviewer and never a hidden or official LeetCode test.
    return {
        'schema': 'tia-grade-review/v1',
        'fixture_sha256': fixture_sha256,
        'fixture_json': fixture_json,
        'fixture_id': fixture['fixture_id'],
        'question_sha256': question_sha256,
        'candidate_event_id': event_id,
        'candidate_sql_sha256': sql_sha256,
        'question_index': question_index,
        'table_summary': [{'name': x['name'], 'rows': len(x['rows'])} for x in fixture['tables']],
        'expected_row_count': len(fixture['expected']['rows']),
        'official_hidden_tests': False,
        'status': 'AWAITING_NATIVE_HUMAN_APPROVAL',
    }


def find_approved_pg_config():
    for candidate in APPROVED_PG_CONFIG:
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    raise GradingBindingError('POSTGRES_SERVER_NOT_AVAILABLE')


def verify_grade_receipt(observation, review):
    if (type(observation) is not dict or set(observation) !=
            {'result', 'finished_tick_seconds', 'finished_wall_seconds'}):
        raise GradingBindingError('INVALID_GRADE_EVIDENCE')
    for key in ('finished_tick_seconds', 'finished_wall_seconds'):
        value = observation[key]
        if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1e12:
            raise GradingBindingError('INVALID_GRADE_EVIDENCE')
    result = observation['result']
    if type(result) is not dict or result.get('correctness') not in ('VERIFIED_LOCAL_FIXTURE', 'NOT_VERIFIED'):
        raise GradingBindingError('INVALID_GRADE_EVIDENCE')
    if any(result.get(k) != review[k] for k in
           ('question_sha256', 'fixture_sha256', 'candidate_sql_sha256')):
        raise GradingBindingError('GRADE_BINDING_MISMATCH')
    if result.get('official_hidden_tests') is not False:
        raise GradingBindingError('INVALID_GRADE_EVIDENCE')
    verdict = result.get('result')
    if type(verdict) is not dict or verdict.get('status') not in (
            'PASSED', 'FAILED', 'EXECUTION_ERROR', 'NOT_VERIFIED'):
        raise GradingBindingError('INVALID_GRADE_EVIDENCE')
    if result['correctness'] == 'VERIFIED_LOCAL_FIXTURE':
        if (result.get('source') != 'EPHEMERAL_POSTGRESQL_LOCAL' or
                verdict['status'] not in ('PASSED', 'FAILED', 'EXECUTION_ERROR') or
                result.get('total_approved_fixtures') != 1 or
                result.get('passed_fixtures') not in (0, 1) or
                (verdict['status'] == 'PASSED') != (result['passed_fixtures'] == 1)):
            raise GradingBindingError('INVALID_GRADE_EVIDENCE')
    elif verdict['status'] != 'NOT_VERIFIED' or result.get('passed_fixtures') != 0:
        raise GradingBindingError('INVALID_GRADE_EVIDENCE')
    return True
