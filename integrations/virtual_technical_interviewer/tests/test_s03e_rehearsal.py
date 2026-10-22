"""S03-E1 host-driven three-question, multi-turn contract; no paid HTTP calls."""
import copy
import json
import tempfile
import unittest

from tia_runtime.app_host import TutorialHost


def question(index):
    return json.dumps({
        'problem_statement': f'Question {index}: compute a distinct keyed rollup without duplicates.',
        'task': f'Explain and implement aggregate solution for dataset number {index}.',
        'schema': f'Orders{index}(order_id INTEGER, customer_id INTEGER, amount DECIMAL)',
        'example_input': '[(1, 2, 3)]', 'expected_output': '[(2, 3)]',
        'environment': 'POSTGRESQL', 'source': 'LEETCODE',
        'constraints': 'A row per order', 'source_reference': '',
    })


class RehearsalE1Tests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.host = await TutorialHost.open(self.directory.name)
        self.serial = 0
        self.rev = 0

    async def asyncTearDown(self):
        self.host.close()
        self.directory.cleanup()

    async def cmd(self, action, params=None, expected=True):
        self.serial += 1
        reply = await self.host.handle({'id': f'e1-{self.serial}', 'action': action, 'params': params or {}})
        self.assertEqual(reply['ok'], expected, reply.get('error'))
        return reply

    async def setup_three(self):
        await self.cmd('choose_real')
        await self.cmd('setup_continue')
        await self.cmd('setup_config', {'config': {
            'technical_environment': 'POSTGRESQL', 'duration_minutes': 45,
            'difficulty': 'HARD', 'question_source': 'BYOQ',
            'interviewer_mechanism': 'STRICT_CHALLENGING',
        }})
        for index in range(3):
            response = await self.cmd('setup_question_set', {
                'index': index, 'raw_text': question(index), 'source': 'LEETCODE'})
            review = response['state']['setup_questions'][index]
            await self.cmd('setup_question_confirm', {
                'index': index, 'fields': copy.deepcopy(review['fields']),
                'raw_sha256': review['raw_sha256']})
        return self.host.state()

    async def start(self):
        await self.setup_three()
        return await self.cmd('rehearsal_start')

    async def model(self, operation='verify', kind='clarify', text='', answer='Synthetic host-governed response'):
        self.rev += 1
        req = f'mock-{self.rev}'
        generation = 'synthetic-generation'
        prepared = (await self.cmd('native_prepare_preview', {
            'request_id': req, 'generation': generation,
            'operation': operation, 'kind': kind, 'text': text,
            'mechanism': 'STRICT_CHALLENGING',
        }))['prepared']
        committed = await self.cmd('native_commit_preview', {
            'transaction_id': prepared['transaction_id'], 'request_id': req,
            'generation': generation, 'reply': {'reply': answer},
            'model': 'synthetic-mock', 'usage': None,
        })
        return prepared, committed

    async def test_three_verified_questions_multi_turn_and_completion(self):
        state = (await self.start())['state']
        self.assertEqual(state['rehearsal']['status'], 'ACTIVE')
        self.assertEqual(state['screen'], 'API_PORTAL')
        for index in range(3):
            prepared, reply = await self.model()
            context = json.loads(prepared['input'])
            self.assertIn(f'Orders{index}', context['question']['schema'])
            self.assertEqual(context['question']['environment'], 'POSTGRESQL')
            self.assertFalse(reply['state']['live_preview']['full_interview_authorized'])
            self.assertEqual(reply['state']['live_preview']['candidate_turn_limit'], 4)
            for turn in range(4):
                prepared, reply = await self.model('reply', 'plan', f'Question {index}, revision {turn}')
                self.assertEqual(reply['state']['live_preview']['candidate_turns_used'], turn + 1)
                self.assertEqual(reply['state']['live_preview']['can_send'], turn < 3)
                self.assertNotIn('grading_authorized', prepared['input'])
            closed = (await self.cmd('rehearsal_submit'))['state']
            self.assertEqual(len(closed['rehearsal']['results']), index + 1)
            result = closed['rehearsal']['results'][-1]
            self.assertEqual(result['outcome'], 'DISCUSSION_ONLY')
            self.assertEqual(result['session']['receipt']['execution_status'], 'NOT_RUN')
            self.assertEqual(result['session']['receipt']['assessment']['technical']['status'], 'NOT_SCORED')
        self.assertEqual(closed['rehearsal']['status'], 'COMPLETE')
        self.assertEqual(closed['screen'], 'REHEARSAL_COMPLETE')
        self.assertEqual((await self.cmd('export'))['export']['provenance'], 'THREE_QUESTION_REHEARSAL_UNSCORED')

    async def test_no_formal_launch_and_no_setup_mutation_while_running(self):
        await self.start()
        await self.cmd('setup_launch', expected=False)
        await self.cmd('setup_back', expected=False)
        await self.cmd('choose_real', expected=False)
        await self.model()
        await self.cmd('practice_start', {'index': 0, 'content_sha256': self.host.setup_questions[0]['content_sha256']}, expected=False)
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 0)

    async def test_skip_without_verified_model_request_is_allowed_and_provenance_truthful(self):
        await self.start()
        for i in range(3):
            state = (await self.cmd('rehearsal_skip'))['state']
            self.assertEqual(state['rehearsal']['results'][-1]['outcome'], 'SKIPPED')
            self.assertIsNone(state['rehearsal']['results'][-1]['session'])
        self.assertEqual(state['rehearsal']['status'], 'COMPLETE')
        self.assertEqual(state['rehearsal']['formal_exam_authorized'], False)

    async def test_pending_native_request_blocks_finish_and_double_commit(self):
        await self.start()
        self.rev += 1
        prepared = (await self.cmd('native_prepare_preview', {
            'request_id': 'pending-1', 'generation': 'synthetic-generation',
            'operation': 'verify', 'kind': 'clarify', 'text': '',
            'mechanism': 'STRICT_CHALLENGING',
        }))['prepared']
        await self.cmd('rehearsal_submit', expected=False)
        await self.cmd('native_commit_preview', {
            'transaction_id': prepared['transaction_id'], 'request_id': 'pending-1',
            'generation': 'synthetic-generation', 'reply': {'reply': 'hi'},
            'model': 'synthetic-mock', 'usage': None,
        })
        await self.cmd('native_commit_preview', {
            'transaction_id': prepared['transaction_id'], 'request_id': 'pending-1',
            'generation': 'synthetic-generation', 'reply': {'reply': 'hi'},
            'model': 'synthetic-mock', 'usage': None,
        }, expected=False)
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 0)

    async def test_cancel_then_retry_has_single_candidate_evidence(self):
        await self.start()
        await self.model()
        self.rev += 1
        params = {'request_id': 'req-cancel', 'generation': 'synthetic-generation',
                  'operation': 'reply', 'kind': 'plan', 'text': 'my durable plan',
                  'mechanism': 'STRICT_CHALLENGING'}
        await self.cmd('native_prepare_preview', params)
        await self.cmd('native_cancel_preview')
        params['request_id'] = 'req-retry'
        prepared = (await self.cmd('native_prepare_preview', params))['prepared']
        await self.cmd('native_commit_preview', {
            'transaction_id': prepared['transaction_id'], 'request_id': 'req-retry',
            'generation': 'synthetic-generation', 'reply': {'reply': 'Please explain.'},
            'model': 'synthetic-mock', 'usage': None,
        })
        state = self.host.state()['live_preview']
        self.assertEqual(state['candidate_turns_used'], 1)
        self.assertIsNone(state['retry_input'])
        self.assertTrue(state['can_send'])

    async def test_replay_restores_frozen_history_without_paid_calls(self):
        await self.start()
        await self.model()
        await self.model('reply', 'clarify', 'A bounded question')
        await self.cmd('rehearsal_submit')
        expected = self.host.state()['rehearsal']
        self.host.close()
        self.host = await TutorialHost.open(self.directory.name)
        restored = self.host.state()['rehearsal']
        self.assertEqual(restored, expected)
        self.assertEqual(restored['current_index'], 1)
        await self.model()
        self.assertIn('Orders1', self.host.state()['live_preview']['question']['schema'])

    async def test_source_requires_three_distinct_confirmed_questions(self):
        await self.cmd('rehearsal_start', expected=False)
        await self.setup_three()
        original = self.host.setup_questions[1]
        self.host.setup_questions[1] = copy.deepcopy(self.host.setup_questions[0])
        result = (await self.cmd('rehearsal_start', expected=False))
        self.assertEqual(result['error'], 'REHEARSAL_QUESTIONS_NOT_CONFIRMED')
        self.host.setup_questions[1] = original

    async def test_existing_single_turn_preview_not_modified(self):
        await self.setup_three()
        review = self.host.setup_questions[0]
        await self.cmd('practice_start', {'index': 0, 'content_sha256': review['content_sha256']})
        await self.model()
        await self.model('reply', 'plan', 'one turn')
        self.assertEqual(self.host.state()['live_preview']['candidate_turn_limit'], 1)
        self.assertFalse(self.host.state()['live_preview']['can_send'])
        await self.cmd('native_prepare_preview', {
            'request_id': 'extra', 'generation': 'synthetic-generation',
            'operation': 'reply', 'kind': 'plan', 'text': 'another turn',
            'mechanism': 'STRICT_CHALLENGING'}, expected=False)


if __name__ == '__main__': unittest.main()
