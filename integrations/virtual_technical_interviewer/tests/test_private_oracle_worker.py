"""Private reference boundary, source/approval bindings and sanitized execution."""
import copy
import hashlib
import json
import unittest
import os
import subprocess
import sys
from pathlib import Path
from tia_runtime.grading_binding import find_approved_pg_config
from tia_runtime.private_oracle_worker import verify_request
from tia_runtime.sql_accuracy import AccuracyError
from tia_runtime.grading_binding import GradingBindingError


def fixture():
    return json.dumps({'schema': 'tia-postgres-fixture/v1', 'fixture_id': 'synthetic-only',
        'question_sha256': 'a' * 64, 'environment': 'POSTGRESQL',
        'tables': [{'name': 'demo', 'columns': [{'name': 'n', 'type': 'INTEGER'}], 'rows': [[7]]}],
        'expected': {'columns': ['n'], 'rows': [[7]], 'order_sensitive': False}})


def packet():
    text = fixture()
    return {'schema': 'tia-private-oracle-request/v1', 'question_sha256': 'a' * 64,
            'fixture_json': text, 'approval_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'references': ['SELECT n FROM demo']}


def fake_runner(blob, code, approval, **kwargs):
    assert kwargs['private_query'] is True
    assert type(blob) is bytes
    return {'question_sha256': 'a' * 64, 'fixture_sha256': approval,
            'candidate_sql_sha256': hashlib.sha256(code.encode()).hexdigest(),
            'source': 'EPHEMERAL_POSTGRESQL_LOCAL', 'correctness': 'VERIFIED_LOCAL_FIXTURE',
            'result': {'status': 'PASSED', 'rows': [['PRIVATE_OUTPUT_DO_NOT_EXPORT']]}}


class PrivateOracleTests(unittest.TestCase):
    def run_request(self, value, runner=fake_runner):
        return verify_request(value, runner=runner, pg_locator=lambda: '/approved/local/pg_config')

    def test_verified_receipt_has_only_bound_metadata(self):
        request = packet(); result = self.run_request(request)
        self.assertEqual(result['references'][0]['status'], 'PASSED')
        text = json.dumps(result)
        for private in ('SELECT', 'PRIVATE_OUTPUT_DO_NOT_EXPORT', 'expected', 'rows', 'demo'):
            self.assertNotIn(private, text)
        self.assertFalse(result['official_hidden_tests'])
        self.assertEqual(result['fixture_sha256'], request['approval_sha256'])

    def test_all_proposed_approaches_checked_independently(self):
        request = packet(); request['references'] *= 3
        result = self.run_request(request)
        self.assertEqual(len(result['references']), 3)
        self.assertEqual([r['index'] for r in result['references']], [0, 1, 2])

    def test_wrong_source_and_unapproved_fixture_fail_before_execution(self):
        for key, value in [('question_sha256', 'b' * 64), ('approval_sha256', 'b' * 64)]:
            request = packet(); request[key] = value
            with self.assertRaises(AccuracyError):
                self.run_request(request, runner=lambda *a, **k: self.fail('must not execute'))

    def test_wrong_result_digest_cannot_be_verified(self):
        def wrong(*args, **kwargs):
            out = fake_runner(*args, **kwargs); out['candidate_sql_sha256'] = 'b' * 64; return out
        result = self.run_request(packet(), runner=wrong)
        self.assertEqual(result['references'][0]['status'], 'NOT_VERIFIED')
        self.assertEqual(result['references'][0]['error'], 'ORACLE_RESULT_BINDING_INVALID')

    def test_missing_postgres_truthfully_not_run(self):
        def unavailable(): raise GradingBindingError('POSTGRES_SERVER_NOT_AVAILABLE')
        result = verify_request(packet(), pg_locator=unavailable)
        self.assertEqual(result['references'][0]['status'], 'NOT_VERIFIED')

    def test_model_cannot_supply_verification_claim_or_command_path(self):
        for key in ('verified', 'pg_config', 'api_key', 'expected'):
            request = packet(); request[key] = True
            with self.assertRaisesRegex(AccuracyError, 'INVALID_ORACLE_REQUEST'):
                self.run_request(request)

    def test_unsafe_reference_rejected_before_runner(self):
        request = packet(); request['references'] = ['DROP TABLE demo']
        with self.assertRaisesRegex(AccuracyError, 'SQL_READ_ONLY'):
            self.run_request(request)

    def test_cancel_does_not_return_partial_verified_receipt(self):
        def cancelled(*args, **kwargs): raise AccuracyError('ORACLE_CANCELLED')
        with self.assertRaisesRegex(AccuracyError, 'ORACLE_CANCELLED'):
            self.run_request(packet(), runner=cancelled)

    def test_error_and_failed_execution_never_become_pass(self):
        for status in ('FAILED', 'EXECUTION_ERROR'):
            def failed(*args, **kwargs):
                out = fake_runner(*args, **kwargs); out['result']['status'] = status; return out
            self.assertEqual(self.run_request(packet(), runner=failed)['references'][0]['status'], status)


    def test_real_stdin_worker_verifies_pass_and_fail_without_leaking_code(self):
        # No model transport. Uses a fresh local PostgreSQL cluster per proposed
        # synthetic approach; validates actual bytes and subprocess contract.
        try:
            find_approved_pg_config()
        except GradingBindingError:
            self.skipTest('Approved local PostgreSQL unavailable')
        if hasattr(os, 'geteuid') and os.geteuid() == 0:
            self.skipTest('PostgreSQL refuses root')
        request = packet()
        request['references'] = ['SELECT n FROM demo', 'SELECT n + 1 AS n FROM demo']
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, '-B', '-m', 'tia_runtime.private_oracle_worker'],
            input=json.dumps(request), text=True, capture_output=True, timeout=115,
            cwd=root, env={'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(result.returncode, 0)
        reply = json.loads(result.stdout)
        self.assertEqual(reply['schema'], 'tia-private-oracle-result/v1')
        self.assertEqual([r['status'] for r in reply['references']], ['PASSED', 'FAILED'])
        for secret in request['references'] + ['demo', 'expected', 'rows']:
            self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertEqual(result.stderr, '')

if __name__ == '__main__': unittest.main()
