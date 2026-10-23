"""E2.5-B: Native-authorized App grading is bound to question, code and fixture.

All PostgreSQL calls in these tests are MOCKED. The separate E2.5-A human
macOS integration gate exercises the actual ephemeral PostgreSQL binary.
"""
import copy
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

from test_s03e_rehearsal import RehearsalE1Tests
from tia_runtime.app_host import TutorialHost
from tia_runtime.grading_binding import GradingBindingError, inspect_binding, verify_grade_receipt


SQL = 'SELECT customer_id, SUM(amount) AS total FROM Orders0 GROUP BY customer_id'


def fixture(qhash, suffix='0'):
    return json.dumps({
        'schema': 'tia-postgres-fixture/v1', 'fixture_id': 'OWNER-Q' + suffix,
        'question_sha256': qhash, 'environment': 'POSTGRESQL',
        'tables': [{'name': 'Orders' + suffix, 'columns': [
            {'name': 'order_id', 'type': 'INTEGER'},
            {'name': 'customer_id', 'type': 'INTEGER'},
            {'name': 'amount', 'type': 'NUMERIC'}], 'rows': [[1, 2, 3]]}],
        'expected': {'columns': ['customer_id', 'total'], 'rows': [[2, 3]],
                     'order_sensitive': False},
    }, separators=(',', ':'))


def witnessed_review(review, passed=True):
    return {
        'source': 'EPHEMERAL_POSTGRESQL_LOCAL',
        'question_sha256': review['question_sha256'],
        'fixture_sha256': review['fixture_sha256'],
        'candidate_sql_sha256': review['candidate_sql_sha256'],
        'official_hidden_tests': False,
        'correctness': 'VERIFIED_LOCAL_FIXTURE',
        'passed_fixtures': int(passed), 'total_approved_fixtures': 1,
        'result': {'status': 'PASSED' if passed else 'FAILED',
                   'reason': 'PASS' if passed else 'ROWS_MISMATCH',
                   'columns': ['customer_id', 'total'], 'rows': [['2', '3']] if passed else [['2','0']],
                   'actual_row_count': 1, 'expected_row_count': 1},
    }


class AppGradingTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = RehearsalE1Tests.asyncSetUp
    asyncTearDown = RehearsalE1Tests.asyncTearDown
    cmd = RehearsalE1Tests.cmd
    setup_three = RehearsalE1Tests.setup_three
    start = RehearsalE1Tests.start
    model = RehearsalE1Tests.model
    async def configure_sql(self, sql=SQL):
        await self.start()
        await self.model()
        await self.model('reply', 'implement', sql)
        return self.host.state()['rehearsal']['questions'][0]['content_sha256']

    async def inspected(self, sql=SQL):
        sha = await self.configure_sql(sql)
        inspected = await self.cmd('grade_inspect', {'fixture_json': fixture(sha)})
        return inspected['state']['grading_review']

    async def grade(self, passed=True):
        inspected = self.host.state()['grading_review']
        with patch('tia_runtime.app_host.find_approved_pg_config', return_value='/fake/pg_config'), \
             patch('tia_runtime.app_host.grade_fixture', return_value=witnessed_review(inspected, passed)) as backend:
            reply = await self.cmd('grade_execute', {'fixture_sha256': inspected['fixture_sha256']})
            backend.assert_called_once()
            return reply

    async def test_grading_requires_active_rehearsal_and_sql_event(self):
        await self.cmd('grade_inspect', {'fixture_json': fixture('a'*64)}, expected=False)
        await self.start()
        await self.cmd('grade_inspect', {'fixture_json': fixture('a'*64)}, expected=False)
        await self.model()
        self.assertEqual((await self.cmd('grade_inspect', {'fixture_json': fixture('a'*64)}, expected=False))['error'],
                         'NO_ACTIVE_SQL_SUBMISSION')

    async def test_fixture_cannot_use_demo_placeholder_or_other_question(self):
        sha = await self.configure_sql()
        self.assertNotEqual(sha, 'a'*64)
        err = (await self.cmd('grade_inspect', {'fixture_json': fixture('a'*64)}, expected=False))['error']
        self.assertEqual(err, 'FIXTURE_QUESTION_MISMATCH')
        await self.cmd('grade_inspect', {'fixture_json': fixture(sha)})

    async def test_explicit_review_and_verified_grade_and_question_receipt(self):
        review = await self.inspected()
        self.assertEqual(review['status'], 'AWAITING_NATIVE_HUMAN_APPROVAL')
        self.assertNotIn('fixture_json', review)
        self.assertEqual(review['question_sha256'], self.host.state()['live_preview']['question']['content_sha256'])
        reply = await self.grade()
        grade = reply['state']['live_preview']['sql_accuracy']
        self.assertEqual(grade['result']['status'], 'PASSED')
        self.assertEqual(grade['passed_fixtures'], 1)
        self.assertEqual(grade['candidate_event_id'], review['candidate_event_id'])
        self.assertEqual(grade['approval_kind'], 'NATIVE_HUMAN_CONFIRMATION')
        self.assertEqual(reply['state']['execution_status'], 'NOT_RUN')  # old tutorial unaffected
        self.assertEqual(reply['state']['live_preview']['technical'], 'NOT_SCORED')
        await self.cmd('grade_execute', {'fixture_sha256': review['fixture_sha256']}, expected=False)
        close = (await self.cmd('rehearsal_submit'))['state']
        self.assertEqual(close['rehearsal']['results'][0]['sql_accuracy'], grade)
        self.assertEqual(close['rehearsal']['results'][0]['execution_status'], 'RUN_LOCAL_FIXTURE')
        self.assertEqual(close['rehearsal']['results'][0]['behavior_metrics']['correctness'], 'VERIFIED_LOCAL_FIXTURE')
        self.assertEqual(close['rehearsal']['current_index'], 1)
        await self.cmd('grade_execute', {'fixture_sha256': review['fixture_sha256']}, expected=False)
        await self.cmd('rehearsal_skip')
        await self.cmd('rehearsal_skip')
        exported = (await self.cmd('export'))['export']
        self.assertEqual(exported['rehearsal']['results'][0]['sql_accuracy'], grade)
        self.assertEqual(exported['rehearsal']['results'][1]['execution_status'], 'NOT_RUN')
        self.assertEqual(exported['rehearsal']['results'][2]['execution_status'], 'NOT_RUN')

    async def test_sql_edit_after_inspection_invalidates_approval(self):
        review = await self.inspected()
        await self.model('reply', 'implement', 'SELECT 0')
        error = (await self.cmd('grade_execute', {'fixture_sha256': review['fixture_sha256']}, expected=False))['error']
        self.assertEqual(error, 'STALE_OR_UNAPPROVED_GRADE')
        self.assertIsNone(self.host.state()['live_preview']['sql_accuracy'])

    async def test_failed_real_query_is_not_a_pass(self):
        await self.inspected()
        result = await self.grade(passed=False)
        self.assertEqual(result['state']['live_preview']['sql_accuracy']['passed_fixtures'], 0)
        self.assertEqual(result['state']['live_preview']['sql_accuracy']['result']['status'], 'FAILED')

    async def test_grading_restore_does_not_execute_postgres_again(self):
        await self.inspected()
        response = await self.grade()
        before = response['state']['live_preview']['sql_accuracy']
        self.host.close()
        with patch('tia_runtime.app_host.grade_fixture', side_effect=AssertionError('replayed SQL!')):
            self.host = await TutorialHost.open(self.directory.name)
        recovered = self.host.state()
        self.assertEqual(recovered['live_preview']['sql_accuracy'], before)
        self.assertIsNone(recovered['recovery_error'])

    async def test_unavailable_postgres_returns_not_verified_not_a_fake_zero_score(self):
        await self.inspected()
        with patch('tia_runtime.app_host.find_approved_pg_config', side_effect=GradingBindingError('POSTGRES_SERVER_NOT_AVAILABLE')):
            result = await self.cmd('grade_execute', {'fixture_sha256': self.host.state()['grading_review']['fixture_sha256']})
        entry = result['state']['live_preview']['sql_accuracy']
        self.assertEqual(entry['correctness'], 'NOT_VERIFIED')
        self.assertEqual(entry['total_approved_fixtures'], 0)
        self.assertEqual(entry['result']['error_code'], 'POSTGRES_SERVER_NOT_AVAILABLE')

    async def test_maximum_fixture_size_and_failure_to_approve_do_not_execute(self):
        await self.configure_sql()
        await self.cmd('grade_inspect', {'fixture_json': 'x'*12001}, expected=False)
        before = len(self.host._journal)
        with patch('tia_runtime.app_host.grade_fixture', side_effect=AssertionError('unexpected execution')):
            await self.cmd('grade_execute', {'fixture_sha256': 'f'*64}, expected=False)
        self.assertIsNone(self.host.state()['live_preview']['sql_accuracy'])
        self.assertNotIn('grades', self.host._rehearsal)
        # Host may journal the elapsed time even for a rejected attempt.

    async def test_pending_native_request_blocks_grading(self):
        await self.configure_sql()
        self.rev += 1
        await self.cmd('native_prepare_preview', {'request_id': 'grade-pending', 'generation': 'synthetic-generation',
                        'operation': 'reply', 'kind': 'help', 'text': 'help', 'mechanism': 'STRICT_CHALLENGING'})
        err = (await self.cmd('grade_inspect', {'fixture_json': fixture(self.host._rehearsal['questions'][0]['content_sha256'])},
                              expected=False))['error']
        self.assertEqual(err, 'NATIVE_REQUEST_PENDING')

    async def test_postgres_result_arriving_after_deadline_is_not_counted(self):
        class Clock:
            value = 10000.0
            def now(self):
                return self.value
            def advance(self, delta):
                self.value += delta
        clock = Clock()
        self.host.close()
        self.host = await TutorialHost.open(self.directory.name, clock=clock.now, wall_clock=clock.now)
        await self.inspected()
        current = self.host.state()['grading_review']
        def delayed(*args, **kwargs):
            clock.advance(2701)
            return witnessed_review(current)
        with patch('tia_runtime.app_host.find_approved_pg_config', return_value='/fake/pg_config'), \
             patch('tia_runtime.app_host.grade_fixture', side_effect=delayed):
            state = (await self.cmd('grade_execute', {'fixture_sha256': current['fixture_sha256']}))['state']
        self.assertEqual(state['rehearsal']['status'], 'TIMED_OUT')
        self.assertEqual(state['rehearsal']['execution'], 'NOT_RUN')
        self.assertFalse(any(r.get('sql_accuracy') for r in state['rehearsal']['results']))
        self.assertNotIn('live_preview', state)
        self.host.close()
        with patch('tia_runtime.app_host.grade_fixture', side_effect=AssertionError('rerun after expiry')):
            self.host = await TutorialHost.open(self.directory.name, clock=clock.now, wall_clock=clock.now)
        self.assertEqual(self.host.state()['rehearsal']['status'], 'TIMED_OUT')
        self.assertEqual(self.host.state()['rehearsal']['execution'], 'NOT_RUN')

    async def test_grade_not_sent_to_interviewer_context(self):
        await self.inspected()
        await self.grade()
        prepared, _ = await self.model('reply', 'plan', 'I will test more cases')
        inputs = json.loads(prepared['input'])
        self.assertNotIn('fixture_id', json.dumps(inputs))
        self.assertNotIn('expected', json.dumps(inputs).lower().replace('expected_output', ''))

    async def test_question_grade_is_never_shared_with_second_question(self):
        await self.inspected()
        await self.grade()
        await self.cmd('rehearsal_submit')
        await self.model()
        await self.model('reply', 'implement', 'SELECT 42')
        state = self.host.state()
        self.assertIsNone(state['live_preview']['sql_accuracy'])
        wrong = (await self.cmd('grade_inspect', {
            'fixture_json': fixture(state['rehearsal']['questions'][0]['content_sha256'])}, expected=False))
        self.assertEqual(wrong['error'], 'FIXTURE_QUESTION_MISMATCH')

    def test_replay_validation_rejects_forged_digest_and_bad_counts(self):
        raw = fixture('a'*64)
        sha = hashlib.sha256(raw.encode()).hexdigest()
        review = inspect_binding(raw, 'a'*64, 'e1', hashlib.sha256(SQL.encode()).hexdigest(), 0)
        evidence = {'result': witnessed_review(review), 'finished_tick_seconds': 2.0, 'finished_wall_seconds': 2.0}
        self.assertTrue(verify_grade_receipt(evidence, review))
        invalid = copy.deepcopy(evidence)
        invalid['result']['official_hidden_tests'] = True
        with self.assertRaises(GradingBindingError):
            verify_grade_receipt(invalid, review)
        invalid = copy.deepcopy(evidence)
        invalid['result']['passed_fixtures'] = 0
        with self.assertRaises(GradingBindingError):
            verify_grade_receipt(invalid, review)


if __name__ == '__main__':
    unittest.main()
