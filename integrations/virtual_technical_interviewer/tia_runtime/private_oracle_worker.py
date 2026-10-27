"""Native-only one-shot reference verifier, NOT the controller/Worker IPC.

Reference code enters stdin and exists only in this short-lived process and a
private ephemeral PostgreSQL transaction. No credentials, paths, DSNs, model
calls, reference text, expected/actual rows or free-form errors are output.
"""
from __future__ import annotations
import hashlib
import json
import signal
import sys
from .persistence import strict_json
from .sql_accuracy import AccuracyError, grade_fixture, validate_fixture, validate_solution
from .grading_binding import GradingBindingError, find_approved_pg_config

SCHEMA = 'tia-private-oracle-request/v1'
MAX_INPUT = 400000


def verify_request(request, *, runner=grade_fixture, pg_locator=find_approved_pg_config):
    if type(request) is not dict or set(request) != {'schema', 'question_sha256', 'fixture_json', 'approval_sha256', 'references'} or request['schema'] != SCHEMA:
        raise AccuracyError('INVALID_ORACLE_REQUEST')
    blob = request['fixture_json']
    if type(blob) is not str:
        raise AccuracyError('INVALID_ORACLE_FIXTURE')
    fixture, digest = validate_fixture(blob.encode('utf-8'))
    if request['question_sha256'] != fixture['question_sha256']:
        raise AccuracyError('ORACLE_QUESTION_MISMATCH')
    if request['approval_sha256'] != digest:
        raise AccuracyError('HUMAN_FIXTURE_APPROVAL_REQUIRED')
    references = request['references']
    if type(references) is not list or not 1 <= len(references) <= 3:
        raise AccuracyError('INVALID_ORACLE_REFERENCES')
    for code in references:
        validate_solution(code)
    rows = []
    try:
        pg_config = pg_locator()
    except GradingBindingError as exc:
        pg_config = None
        unavailable = exc.code
    for index, code in enumerate(references):
        status, error = 'NOT_VERIFIED', None
        if pg_config is None:
            error = unavailable
        else:
            try:
                result = runner(blob.encode('utf-8'), code, digest, pg_config=pg_config, private_query=True)
                if (result.get('question_sha256') != fixture['question_sha256'] or
                        result.get('fixture_sha256') != digest or
                        result.get('candidate_sql_sha256') != hashlib.sha256(code.encode()).hexdigest() or
                        result.get('source') != 'EPHEMERAL_POSTGRESQL_LOCAL' or
                        result.get('correctness') != 'VERIFIED_LOCAL_FIXTURE' or
                        result.get('result', {}).get('status') not in ('PASSED', 'FAILED', 'EXECUTION_ERROR')):
                    raise AccuracyError('ORACLE_RESULT_BINDING_INVALID')
                status = result['result']['status']
            except AccuracyError as exc:
                if exc.code == 'ORACLE_CANCELLED':
                    raise
                error = exc.code
        # Enumerated technical codes only. No PostgreSQL/model error strings.
        rows.append({'index': index, 'reference_sha256': hashlib.sha256(code.encode()).hexdigest(),
                     'status': status, 'error': error})
    return {'schema': 'tia-private-oracle-result/v1', 'question_sha256': fixture['question_sha256'],
            'fixture_sha256': digest, 'source': 'EPHEMERAL_POSTGRESQL_LOCAL',
            'official_hidden_tests': False, 'references': rows}


def main():
    # Interrupted PostgreSQL work unwinds its finally block and shuts down its
    # ephemeral cluster; no retry and no verification receipt on cancellation.
    def cancelled(signum, frame):
        raise AccuracyError('ORACLE_CANCELLED')
    signal.signal(signal.SIGTERM, cancelled)
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if not raw or len(raw) > MAX_INPUT:
            raise AccuracyError('ORACLE_INPUT_LIMIT')
        output = verify_request(strict_json(raw.decode('utf-8')))
    except (AccuracyError, GradingBindingError) as exc:
        output = {'schema': 'tia-private-oracle-error/v1', 'error': exc.code}
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        output = {'schema': 'tia-private-oracle-error/v1', 'error': 'INVALID_ORACLE_REQUEST'}
    sys.stdout.write(json.dumps(output, sort_keys=True, separators=(',', ':')) + '\n')

if __name__ == '__main__':
    main()
