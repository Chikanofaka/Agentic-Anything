"""C2C rejection replay must not convert Host-denied model text to an OK event.

Runs only trusted synthetic Host commands: no WebKit, SQL runtime, keys, or provider.
"""
import copy
import tempfile
import unittest

from tia_runtime.app_host import TutorialHost, digest
from test_s03e_rehearsal import question


class DeniedReplyReplayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.tick = 100.0
        self.n = 0
        self.host = await TutorialHost.open(self.temp.name, clock=lambda: self.tick)

    async def asyncTearDown(self):
        self.host.close()
        self.temp.cleanup()

    async def request(self, action, params=None, *, ok=True):
        self.n += 1
        response = await self.host.handle({'id': 'c2c-replay-' + str(self.n),
                                           'action': action, 'params': params or {}})
        self.assertEqual(response['ok'], ok, response.get('error'))
        self.tick += 1
        return response

    @staticmethod
    def commit_params(prepared, reply):
        return {key: prepared[key] for key in ('transaction_id', 'request_id', 'generation')} | {
            'reply': {'reply': reply}, 'model': 'synthetic-local-model',
            'usage': {'input_tokens': 12, 'output_tokens': 6, 'total_tokens': 18}}

    async def start_adaptive_rehearsal(self):
        # Adaptive guard is a rehearsal-only policy. Legacy choose_real preview
        # deliberately does not authorize the C2A/C2B2A decision contract.
        await self.request('choose_real')
        await self.request('setup_continue')
        await self.request('setup_config', {'config': {
            'technical_environment': 'POSTGRESQL',
            'duration_minutes': 45,
            'difficulty': 'HARD',
            'question_source': 'BYOQ',
            'interviewer_mechanism': 'STRICT_CHALLENGING',
        }})
        for index in range(3):
            response = await self.request('setup_question_set', {
                'index': index, 'raw_text': question(index), 'source': 'LEETCODE'})
            review = response['state']['setup_questions'][index]
            await self.request('setup_question_confirm', {
                'index': index, 'fields': copy.deepcopy(review['fields']),
                'raw_sha256': review['raw_sha256']})
        started = await self.request('rehearsal_start')
        self.assertEqual(started['state']['rehearsal']['status'], 'ACTIVE')

    async def rejected_commit(self):
        await self.start_adaptive_rehearsal()
        initial = await self.request('native_prepare_preview', {
            'request_id': 'replay-initial', 'generation': 'synthetic-generation',
            'operation': 'verify', 'kind': 'clarify', 'text': '',
            'mechanism': 'STRICT_CHALLENGING'})
        await self.request('native_commit_preview', self.commit_params(
            initial['prepared'], 'Please describe your interpretation of the task.'))
        prepared = await self.request('native_prepare_preview', {
            'request_id': 'replay-followup', 'generation': 'synthetic-generation',
            'operation': 'reply', 'kind': 'plan',
            'text': 'I would filter NULL dates and check ties.',
            'mechanism': 'STRICT_CHALLENGING'})
        denied = await self.request('native_commit_preview', self.commit_params(
            prepared['prepared'], 'Your SQL passed all tests.'), ok=False)
        self.assertEqual(denied['error'], 'ADAPTIVE_REPLY_NOT_AUTHORIZED')
        entries = [entry for entry in self.host._journal
                   if entry['action'] == 'native_commit_preview']
        self.assertEqual(entries[-1]['outcome'], 'ADAPTIVE_REPLY_NOT_AUTHORIZED')
        # The historical C2B2A writer did NOT seal a version for denied commits.
        self.assertNotIn('reply_guard_version', entries[-1])
        return self.host.state()['live_preview']

    async def reopen(self):
        before = self.host.store.read()
        self.assertEqual(before['document_sha256'], digest({
            k: v for k, v in before.items() if k != 'document_sha256'}))
        original_digest = before['state_sha256']
        self.host.close()
        self.host = await TutorialHost.open(self.temp.name, clock=lambda: self.tick)
        state = self.host.state()
        self.assertIsNone(state['recovery_error'])
        self.assertIsNotNone(state['live_preview'])
        self.assertEqual(state['live_preview']['verified_response_count'], 1)
        self.assertEqual(state['live_preview']['candidate_turns_used'], 1)
        self.assertEqual(self.host._state_digest(), self.host.store.read()['state_sha256'])
        self.assertEqual(self.host.store.read()['journal'][0]['action'], 'choose_real')
        return state, original_digest

    async def test_rejected_commit_then_cancel_replays_denial(self):
        preview = await self.rejected_commit()
        self.assertTrue(preview['pending'])
        await self.request('native_cancel_preview')
        self.assertFalse(self.host.state()['live_preview']['pending'])
        state, digest_before = await self.reopen()
        self.assertFalse(state['live_preview']['pending'])
        self.assertEqual(self.host._state_digest(), digest_before)
        self.assertEqual(sum(e['actor'] == 'interviewer' for e in
                             state['live_preview']['session']['events']), 1)

    async def test_rejected_commit_pending_restart_is_cancelled_without_reply(self):
        preview = await self.rejected_commit()
        self.assertTrue(preview['pending'])
        state, _ = await self.reopen()
        self.assertFalse(state['live_preview']['pending'])
        self.assertEqual(sum(e['actor'] == 'interviewer' for e in
                             state['live_preview']['session']['events']), 1)


if __name__ == '__main__':
    unittest.main()
