"""P0 SQL attempt ledger: three candidate chances, Host-owned T01.

All database outcomes are mocked. No provider, microphone or PostgreSQL process
is used by this suite.
"""
import copy
import json
import tempfile
import unittest

from tia_runtime.app_host import TutorialHost
from tia_runtime import post_interview_sql as sql


QUESTIONS = (
    ('delivery_first_orders', 'Delivery',
     '| delivery_id | int |\n| customer_id | int |\n| order_date | date |\n| customer_pref_delivery_date | date |'),
    ('monthly_transactions', 'Transactions',
     '| id | int |\n| country | text |\n| state | text |\n| amount | int |\n| trans_date | date |'),
    ('bus_last_person', 'Queue',
     '| person_id | int |\n| person_name | text |\n| weight | int |\n| turn | int |'),
)


def question(index):
    _, table, columns = QUESTIONS[index]
    return json.dumps({'problem_statement': f'Approved SQL task {index}',
        'task': f'Write the requested query for {table}.',
        'schema': f'Table: {table}\n{columns}', 'example_input': 'synthetic rows',
        'expected_output': 'one approved result', 'environment': 'POSTGRESQL',
        'source': 'LEETCODE', 'constraints': 'Use PostgreSQL.', 'source_reference': ''})


class SQLAttemptLedgerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.host = await TutorialHost.open(self.temp.name)
        self.serial = self.model_serial = 0
        await self._setup()

    async def asyncTearDown(self):
        self.host.close(); self.temp.cleanup()

    async def cmd(self, action, params=None, ok=True):
        self.serial += 1
        reply = await self.host.handle({'id': f'ledger-{self.serial}', 'action': action,
                                        'params': params or {}})
        self.assertEqual(reply['ok'], ok, reply.get('error'))
        return reply

    async def _setup(self):
        await self.cmd('choose_real'); await self.cmd('setup_continue')
        await self.cmd('setup_config', {'config': {'technical_environment':'POSTGRESQL',
            'duration_minutes':45, 'difficulty':'HARD', 'question_source':'BYOQ',
            'interviewer_mechanism':'STRICT_CHALLENGING'}})
        for index in range(3):
            state = (await self.cmd('setup_question_set', {'index':index,
                'raw_text':question(index), 'source':'LEETCODE'}))['state']
            review = state['setup_questions'][index]
            await self.cmd('setup_question_confirm', {'index':index,
                'fields':copy.deepcopy(review['fields']), 'raw_sha256':review['raw_sha256']})
        await self.cmd('rehearsal_start', {'continuity_policy':'tia-continuity/v3',
                                           'sql_attempt_policy':'tia-sql-attempts/v1'})
        await self.model()

    async def model(self, operation='verify', kind='clarify', text=''):
        self.model_serial += 1
        request = f'ledger-model-{self.model_serial}'
        prepared = (await self.cmd('native_prepare_preview', {'request_id':request,
            'generation':'ledger-generation', 'operation':operation, 'kind':kind,
            'text':text, 'mechanism':'STRICT_CHALLENGING'}))['prepared']
        return await self.cmd('native_commit_preview', {'transaction_id':prepared['transaction_id'],
            'request_id':request, 'generation':'ledger-generation',
            'reply':{'reply':'Host-governed synthetic interviewer response.'},
            'model':'synthetic-mock', 'usage':None})

    async def implementation(self, text):
        await self.model('reply', 'implement', text)

    async def verdict(self, status, reason):
        index = self.host._rehearsal['current_index']
        suite = QUESTIONS[index][0]
        await self.cmd('post_sql_review', {'question_index':index, 'suite_id':suite})
        review = self.host.state()['post_interview_sql']['review']
        token = f'sql-{self.serial}'
        packet = (await self.cmd('native_prepare_post_sql', {'request_id':token,
            'generation':'ledger-generation', 'review_sha256':review['review_sha256']}))['prepared']
        result = sql.execute(packet, runner=lambda *a,**k:{'result':{'status':status,'reason':reason}},
                             pg_config='synthetic')
        return (await self.cmd('native_commit_post_sql', {'result':result}))['state']

    async def test_first_failure_second_pass_uses_only_passing_submission(self):
        await self.implementation('SELECT broken_one')
        state = await self.verdict('EXECUTION_ERROR', 'QUERY_ERROR')
        first = state['post_interview_sql']['execution_ledger']['0'][0]
        self.assertEqual((first['attempt_number'], first['attempts_remaining'], first['terminal']),
                         (1, 2, False))
        response = await self.cmd('rehearsal_submit', ok=False)
        self.assertEqual(response['error'], 'SQL_RESUBMISSION_REQUIRED')
        await self.implementation('SELECT passing_two')
        response = await self.cmd('rehearsal_submit', ok=False)
        self.assertEqual(response['error'], 'SQL_VERIFICATION_REQUIRED')
        state = await self.verdict('PASSED', 'PASS')
        second = state['post_interview_sql']['execution_ledger']['0'][-1]
        self.assertEqual((second['attempt_number'], second['t01_provisional_points']), (2, 18))
        state = (await self.cmd('rehearsal_submit'))['state']
        self.assertEqual(state['rehearsal']['current_index'], 1)
        self.assertEqual(state['evidence_scorecard']['questions'][0]['accuracy']['status'], 'PASSED')

    async def test_three_candidate_query_errors_freeze_zero_and_close(self):
        for attempt in range(1, 4):
            await self.implementation(f'SELECT broken_{attempt}')
            state = await self.verdict('EXECUTION_ERROR', 'QUERY_ERROR')
            row = state['post_interview_sql']['execution_ledger']['0'][-1]
            self.assertEqual(row['attempt_number'], attempt)
            self.assertEqual(row['attempts_remaining'], 3-attempt)
        self.assertTrue(row['terminal'])
        self.assertEqual((row['t01_authority'], row['t01_provisional_points']), ('OBSERVED_ZERO', 0))
        state = (await self.cmd('rehearsal_submit'))['state']
        self.assertEqual(state['rehearsal']['current_index'], 1)
        self.assertEqual(state['evidence_scorecard']['questions'][0]['accuracy']['status'], 'EXECUTION_ERROR')

    async def test_three_failed_test_runs_freeze_zero(self):
        for attempt in range(1, 4):
            await self.implementation(f'SELECT wrong_rows_{attempt}')
            state = await self.verdict('FAILED', 'ROWS_MISMATCH')
        row = state['post_interview_sql']['execution_ledger']['0'][-1]
        self.assertEqual((row['status'], row['attempt_number'], row['t01_provisional_points']),
                         ('FAILED_TESTS', 3, 0))

    async def test_infrastructure_failure_does_not_consume_attempt(self):
        await self.implementation('SELECT retry_same_sql')
        state = await self.verdict('NOT_VERIFIED', 'POSTGRES_SERVER_NOT_AVAILABLE')
        infra = state['post_interview_sql']['execution_ledger']['0'][0]
        self.assertEqual((infra['attempt_number'], infra['attempts_remaining'],
                          infra['consumes_attempt'], infra['failure_owner']),
                         (1, 3, False, 'INFRASTRUCTURE'))
        self.assertEqual(state['post_interview_sql']['results']['0']['failure_owner'], 'INFRASTRUCTURE')
        state = await self.verdict('PASSED', 'PASS')
        row = state['post_interview_sql']['execution_ledger']['0'][-1]
        self.assertEqual((row['attempt_number'], row['attempts_remaining']), (1, 2))

    async def test_first_two_failures_third_pass_preserves_history(self):
        expected = (('EXECUTION_ERROR', 'QUERY_ERROR', 'CANDIDATE_QUERY_ERROR'),
                    ('FAILED', 'ROWS_MISMATCH', 'FAILED_TESTS'),
                    ('PASSED', 'PASS', 'PASSED'))
        for attempt, (native_status, reason, canonical) in enumerate(expected, 1):
            await self.implementation(f'SELECT revision_{attempt}')
            state = await self.verdict(native_status, reason)
            row = state['post_interview_sql']['execution_ledger']['0'][-1]
            self.assertEqual((row['attempt_number'], row['status']), (attempt, canonical))
        history = state['post_interview_sql']['execution_ledger']['0']
        self.assertEqual([row['status'] for row in history],
                         ['CANDIDATE_QUERY_ERROR', 'FAILED_TESTS', 'PASSED'])
        self.assertEqual(history[-1]['t01_provisional_points'], 18)
        state = (await self.cmd('rehearsal_submit'))['state']
        self.assertEqual(state['evidence_scorecard']['questions'][0]['accuracy']['status'], 'PASSED')

    async def test_skip_after_candidate_failure_freezes_zero(self):
        await self.implementation('SELECT candidate_failure')
        await self.verdict('FAILED', 'ROWS_MISMATCH')
        state = (await self.cmd('rehearsal_skip'))['state']
        row = state['post_interview_sql']['execution_ledger']['0'][-1]
        self.assertEqual((row['terminal'], row['attempts_remaining'], row['t01_provisional_points']),
                         (True, 0, 0))
        self.assertEqual(state['evidence_scorecard']['questions'][0]['accuracy']['status'], 'FAILED')

    async def test_skip_without_candidate_verdict_remains_not_observed(self):
        state = (await self.cmd('rehearsal_skip'))['state']
        self.assertEqual(state['post_interview_sql']['execution_ledger']['0'], [])
        self.assertEqual(state['evidence_scorecard']['questions'][0]['accuracy']['status'], 'NOT_VERIFIED')

    async def test_infrastructure_failure_then_skip_never_becomes_zero(self):
        await self.implementation('SELECT infrastructure_retry')
        await self.verdict('NOT_VERIFIED', 'POSTGRES_SERVER_NOT_AVAILABLE')
        state = (await self.cmd('rehearsal_skip'))['state']
        row = state['post_interview_sql']['execution_ledger']['0'][-1]
        self.assertEqual((row['failure_owner'], row['terminal'], row['t01_provisional_points']),
                         ('INFRASTRUCTURE', False, None))
        self.assertEqual(state['evidence_scorecard']['questions'][0]['accuracy']['status'], 'NOT_VERIFIED')


if __name__ == '__main__':
    unittest.main()
