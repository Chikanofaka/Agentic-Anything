"""S03-E2: deterministic hard deadlines and journalled wall/monotonic timing."""
import copy
import json
import tempfile
import unittest

from tia_runtime.app_host import TutorialHost
from tia_runtime.time_intelligence import LIMIT_SECONDS


class FakeClocks:
    def __init__(self):
        self.monotonic = 100.0
        self.wall = 1792800000.0

    def advance(self, seconds, *, active=True):
        self.wall += seconds
        if active:
            self.monotonic += seconds


class TimeIntelligenceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.clocks = FakeClocks()
        self.host = await TutorialHost.open(
            self.temp.name, clock=lambda: self.clocks.monotonic,
            wall_clock=lambda: self.clocks.wall)
        self.n = 0

    async def asyncTearDown(self):
        self.host.close()
        self.temp.cleanup()

    async def cmd(self, action, params=None, *, ok=True):
        self.n += 1
        result = await self.host.handle({'id': 'time-' + str(self.n), 'action': action, 'params': params or {}})
        self.assertEqual(result['ok'], ok, result.get('error'))
        return result

    async def start(self):
        await self.cmd('choose_real')
        await self.cmd('setup_continue')
        await self.cmd('setup_config', {'config': {
            'technical_environment': 'POSTGRESQL', 'duration_minutes': 45,
            'difficulty': 'HARD', 'question_source': 'BYOQ',
            'interviewer_mechanism': 'STRICT_CHALLENGING',
        }})
        for i in range(3):
            raw = json.dumps({
                'problem_statement': f'Question {i}: find aggregated values.',
                'task': f'Explain the distinct aggregation for Q{i}.',
                'schema': f'Orders{i}(id INTEGER, customer_id INTEGER, amount DECIMAL)',
                'example_input': '[(1,2,3)]', 'expected_output': '[(2,3)]',
                'environment': 'POSTGRESQL', 'source': 'LEETCODE',
                'constraints': 'One per customer', 'source_reference': '',
            })
            response = await self.cmd('setup_question_set', {'index': i, 'raw_text': raw, 'source': 'LEETCODE'})
            review = response['state']['setup_questions'][i]
            await self.cmd('setup_question_confirm', {
                'index': i, 'fields': copy.deepcopy(review['fields']), 'raw_sha256': review['raw_sha256']})
        return (await self.cmd('rehearsal_start'))['state']

    async def model(self, *, operation='verify', request='req1'):
        params = {'request_id': request, 'generation': 'test-generation', 'operation': operation,
                  'kind': 'plan' if operation == 'reply' else 'clarify',
                  'text': 'candidate answer' if operation == 'reply' else '',
                  'mechanism': 'STRICT_CHALLENGING'}
        prepared = (await self.cmd('native_prepare_preview', params))['prepared']
        return (await self.cmd('native_commit_preview', {
            'transaction_id': prepared['transaction_id'], 'request_id': request,
            'generation': 'test-generation', 'reply': {'reply': 'A synthetic model answer'},
            'model': 'synthetic-mock', 'usage': None,
        }))['state']

    async def reopen(self):
        self.host.close()
        self.host = await TutorialHost.open(self.temp.name,
            clock=lambda: self.clocks.monotonic, wall_clock=lambda: self.clocks.wall)

    async def test_three_question_elapsed_intervals_and_export(self):
        state = await self.start()
        self.assertEqual(state['rehearsal']['timing']['limit_seconds'], 2700)
        self.assertFalse(state['rehearsal']['timing']['started'])
        await self.model()
        self.clocks.advance(120)
        await self.cmd('rehearsal_tick')
        await self.cmd('rehearsal_submit')
        self.clocks.advance(240)
        await self.cmd('rehearsal_skip')
        self.clocks.advance(360)
        state = (await self.cmd('rehearsal_submit'))['state']
        self.assertEqual(state['rehearsal']['status'], 'COMPLETE')
        self.assertEqual(state['rehearsal']['timing']['elapsed_seconds'], 720)
        self.assertEqual([q['elapsed_seconds'] for q in state['rehearsal']['timing']['questions']], [120, 240, 360])
        self.assertEqual(state['rehearsal']['results'][1]['outcome'], 'SKIPPED')
        exported = (await self.cmd('export'))['export']
        self.assertEqual(exported['timing']['elapsed_seconds'], 720)
        self.assertFalse(exported['timing']['certified'])
        self.assertEqual(exported['execution_status'], 'NOT_RUN')

    async def test_model_wait_is_a_subset_of_overall_wall_time(self):
        await self.start()
        await self.model(request='open')
        self.clocks.advance(10)
        prepared = (await self.cmd('native_prepare_preview', {
            'request_id': 'p1', 'generation': 'test-generation', 'operation': 'reply',
            'kind': 'plan', 'text': 'working hypothesis', 'mechanism': 'STRICT_CHALLENGING'}))['prepared']
        self.clocks.advance(13)
        state = (await self.cmd('native_commit_preview', {
            'transaction_id': prepared['transaction_id'], 'request_id': 'p1',
            'generation': 'test-generation', 'reply': {'reply': 'Synthetic question'},
            'model': 'mock', 'usage': None}))['state']
        time = state['rehearsal']['timing']
        self.assertEqual(time['elapsed_seconds'], 23)
        self.assertEqual(time['model_wait_seconds'], 13)
        self.clocks.advance(17)
        state = (await self.cmd('rehearsal_submit'))['state']
        self.assertEqual(state['rehearsal']['results'][0]['time_metrics']['elapsed_seconds'], 40)
        self.assertEqual(state['rehearsal']['results'][0]['time_metrics']['model_wait_seconds'], 13)

    async def test_hard_45minute_deadline_finishes_all_three(self):
        await self.start()
        await self.model()
        self.clocks.advance(LIMIT_SECONDS)
        state = (await self.cmd('rehearsal_tick'))['state']
        self.assertEqual(state['rehearsal']['status'], 'TIMED_OUT')
        self.assertEqual(state['screen'], 'REHEARSAL_COMPLETE')
        self.assertEqual([r['outcome'] for r in state['rehearsal']['results']],
                         ['TIMED_OUT', 'NOT_REACHED', 'NOT_REACHED'])
        self.assertEqual(state['rehearsal']['timing']['elapsed_seconds'], LIMIT_SECONDS)
        await self.cmd('native_prepare_preview', {
            'request_id': 'late', 'generation': 'test-generation',
            'operation': 'verify', 'kind': 'clarify', 'text': '',
            'mechanism': 'STRICT_CHALLENGING'}, ok=False)
        self.assertEqual(len(self.host.state()['rehearsal']['results']), 3)

    async def test_late_provider_completion_cannot_commit_and_does_not_score(self):
        await self.start()
        await self.model(request='opening')
        prepared = (await self.cmd('native_prepare_preview', {
            'request_id': 'pending', 'generation': 'test-generation',
            'operation': 'reply', 'kind': 'plan', 'text': 'candidate reasoning',
            'mechanism': 'STRICT_CHALLENGING'}))['prepared']
        self.clocks.advance(LIMIT_SECONDS + 90)
        response = await self.cmd('native_commit_preview', {
            'transaction_id': prepared['transaction_id'], 'request_id': 'pending',
            'generation': 'test-generation', 'reply': {'reply': 'late and invalid'},
            'model': 'mock', 'usage': None}, ok=False)
        self.assertEqual(response['error'], 'REHEARSAL_TIME_LIMIT')
        self.assertEqual(response['state']['rehearsal']['status'], 'TIMED_OUT')
        self.assertEqual(response['state']['rehearsal']['timing']['model_wait_seconds'], LIMIT_SECONDS)
        self.assertEqual(response['state']['rehearsal']['results'][0]['session']['receipt']['live_model_used'], True)
        self.assertEqual(sum(e['actor'] == 'interviewer' for e in response['state']['rehearsal']['results'][0]['session']['events']), 1)
        self.assertEqual(response['state']['rehearsal']['results'][0]['session']['receipt']['assessment']['technical']['status'], 'NOT_SCORED')

    async def test_process_downtime_counts_toward_deadline(self):
        await self.start()
        await self.model()
        self.clocks.advance(30)
        await self.cmd('rehearsal_tick')
        self.clocks.advance(3000, active=False)
        await self.reopen()
        state = self.host.state()
        self.assertEqual(state['rehearsal']['status'], 'TIMED_OUT')
        self.assertEqual(state['rehearsal']['timing']['elapsed_seconds'], LIMIT_SECONDS)
        self.assertIsNone(state.get('activation'))

    async def test_short_recovery_retains_timing_and_does_not_forge_calls(self):
        await self.start()
        await self.model()
        self.clocks.advance(5)
        await self.cmd('rehearsal_tick')
        self.clocks.advance(60, active=False)
        await self.reopen()
        state = self.host.state()['rehearsal']
        self.assertEqual(state['timing']['elapsed_seconds'], 65)
        self.assertEqual(state['timing']['current_question'], 0)
        self.assertEqual(state['status'], 'ACTIVE')
        await self.cmd('rehearsal_submit')
        self.assertEqual(self.host.state()['rehearsal']['results'][0]['time_metrics']['elapsed_seconds'], 65)

    async def test_clock_rollback_fail_closed(self):
        await self.start()
        await self.model()
        self.clocks.advance(30)
        await self.cmd('rehearsal_tick')
        self.clocks.wall -= 10
        state = (await self.cmd('rehearsal_tick'))['state']
        self.assertEqual(state['rehearsal']['status'], 'CLOCK_INTEGRITY_HOLD')
        self.assertEqual(state['rehearsal']['timing']['integrity'], 'WALL_ROLLBACK_HOLD')
        self.assertEqual(state['rehearsal']['results'][0]['outcome'], 'CLOCK_INTEGRITY_HOLD')
        await self.reopen()
        self.assertEqual(self.host.state()['rehearsal']['status'], 'CLOCK_INTEGRITY_HOLD')

    async def test_monotonic_elapsed_prevents_small_wall_rollback(self):
        await self.start()
        await self.model()
        self.clocks.monotonic += 17
        self.clocks.wall += 16
        await self.cmd('rehearsal_tick')
        self.assertEqual(self.host.state()['rehearsal']['timing']['elapsed_seconds'], 17)
        self.assertEqual(self.host.state()['rehearsal']['timing']['integrity'], 'LOCAL_UNATTESTED')

    async def test_portal_setup_time_does_not_debit_interview(self):
        await self.start()
        self.clocks.advance(3600)
        state = (await self.cmd('rehearsal_tick'))['state']
        self.assertEqual(state['rehearsal']['status'], 'ACTIVE')
        self.assertFalse(state['rehearsal']['timing']['started'])
        self.assertEqual(state['rehearsal']['timing']['elapsed_seconds'], 0)
        await self.model()
        self.assertEqual(self.host.state()['rehearsal']['timing']['elapsed_seconds'], 0)
        self.clocks.advance(14)
        await self.cmd('rehearsal_tick')
        self.assertEqual(self.host.state()['rehearsal']['timing']['elapsed_seconds'], 14)

    async def test_pending_model_is_cancelled_after_restart_without_forging_reply(self):
        await self.start()
        await self.model(request='start')
        prepared = (await self.cmd('native_prepare_preview', {
            'request_id': 'awaiting', 'generation': 'test-generation',
            'operation': 'reply', 'kind': 'plan', 'text': 'durable reasoning',
            'mechanism': 'STRICT_CHALLENGING'}))['prepared']
        self.clocks.advance(38, active=False)
        await self.reopen()
        state = self.host.state()
        self.assertIsNone(state.get('recovery_error'))
        self.assertEqual(state['rehearsal']['timing']['model_wait_seconds'], 38)
        self.assertFalse(state['rehearsal']['timing']['model_request_pending'])
        self.assertIsNotNone(state['live_preview']['retry_input'])
        invalid = await self.cmd('native_commit_preview', {
            'transaction_id': prepared['transaction_id'], 'request_id': 'awaiting',
            'generation': 'test-generation', 'reply': {'reply': 'stale reply'},
            'model': 'synthetic-mock', 'usage': None,
        }, ok=False)
        self.assertEqual(invalid['error'], 'STALE_NATIVE_REPLY')
        self.assertEqual(state['live_preview']['verified_response_count'], 1)

    async def test_legacy_e1_save_still_loads_without_timings(self):
        await self.start()
        # Simulate an E1 save made before journal wall samples existed.
        self.host._rehearsal.pop('timing')
        self.host._journal[-1].pop('wall_seconds')
        self.host._persist()
        await self.reopen()
        self.assertEqual(self.host.state()['rehearsal']['status'], 'ACTIVE')
        self.assertNotIn('timing', self.host.state()['rehearsal'])

if __name__ == '__main__':
    unittest.main()
