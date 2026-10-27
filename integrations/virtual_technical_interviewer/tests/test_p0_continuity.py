"""P0-01: continuous questions, independent deadlines and exact legacy replay.

All provider responses are local fixtures; no HTTP or credential is used.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tia_runtime.app_host import TutorialHost
from tia_runtime.host_adaptive_bridge import seconds_remaining
import test_s03e_rehearsal as legacy_rehearsal
import test_s03e_app_grading as legacy_grading
from test_s03e_time_intelligence import FakeClocks


class ContinuityV3Tests(unittest.IsolatedAsyncioTestCase):
    cmd = legacy_rehearsal.RehearsalE1Tests.cmd
    setup_three = legacy_rehearsal.RehearsalE1Tests.setup_three
    model = legacy_rehearsal.RehearsalE1Tests.model

    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.clocks = FakeClocks()
        self.host = await TutorialHost.open(self.directory.name,
            clock=lambda: self.clocks.monotonic, wall_clock=lambda: self.clocks.wall)
        self.serial = self.rev = 0

    async def asyncTearDown(self):
        self.host.close()
        self.directory.cleanup()

    async def start(self):
        await self.setup_three()
        await self.cmd('rehearsal_start', {'continuity_policy': 'tia-continuity/v3'})
        await self.model()

    async def reopen(self):
        self.host.close()
        self.host = await TutorialHost.open(self.directory.name,
            clock=lambda: self.clocks.monotonic, wall_clock=lambda: self.clocks.wall)
        self.assertIsNone(self.host.state().get('recovery_error'))

    async def test_four_turns_are_not_a_question_boundary(self):
        await self.start()
        for turn in range(9):
            _, response = await self.model('reply', 'clarify', f'Candidate clarification {turn}')
        state = response['state']
        self.assertIsNone(state['live_preview']['candidate_turn_limit'])
        self.assertIsNone(state['rehearsal']['max_turns_per_question'])
        self.assertEqual(state['live_preview']['candidate_turns_used'], 9)
        self.assertTrue(state['live_preview']['can_send'])
        self.assertEqual(state['rehearsal']['current_index'], 0)
        self.assertEqual(state['rehearsal']['results'], [])
        digest = self.host._state_digest()
        await self.reopen()
        self.assertEqual(self.host._state_digest(), digest)

    async def test_controller_event_limit_is_not_a_replacement_turn_cap(self):
        await self.start()
        controller = self.host._live_controller
        self.assertIsNone(controller.config.max_events)
        for turn in range(150):
            controller.candidate_action('clarify', f'Continuous event {turn}')
        self.assertEqual(controller.phase, 'INTERVIEWING')
        self.assertIsNone(controller.receipt)
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 0)

    async def test_journal_count_is_not_a_replacement_turn_cap_and_replays(self):
        await self.start()
        # Exercise the real count boundary with harmless local language actions;
        # no provider, transcript mutation, or artificial enlarged count constant.
        with patch.object(self.host, '_persist'):
            while len(self.host._journal) <= 512:
                await self.cmd('language', {'language': 'en'})
        self.host._persist()
        await self.reopen()
        self.assertGreater(len(self.host._journal), 512)
        self.assertTrue(self.host.state()['live_preview']['can_send'])
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 0)

    async def test_only_submit_skip_or_timeout_advances(self):
        await self.start()
        response = await self.cmd('preview_close', expected=False)
        self.assertEqual(response['error'], 'REHEARSAL_EXIT_REQUIRES_SUBMIT_SKIP_OR_TIMEOUT')
        await self.cmd('rehearsal_submit', expected=False)
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 0)
        await self.model('reply', 'implement', 'SELECT 1;')
        await self.cmd('rehearsal_submit')
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 1)
        await self.cmd('rehearsal_skip')
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 2)
        await self.model()
        self.clocks.advance(900)
        response = await self.cmd('rehearsal_tick')
        self.assertEqual(response['state']['rehearsal']['status'], 'COMPLETE')
        self.assertEqual([r['outcome'] for r in response['state']['rehearsal']['results']],
                         ['SUBMITTED_UNVERIFIED', 'SKIPPED', 'TIMED_OUT'])

    async def test_each_question_gets_900_seconds_and_setup_is_not_debited(self):
        await self.start()
        for index in range(3):
            self.assertEqual(seconds_remaining(self.host._rehearsal), 900)
            self.clocks.advance(899)
            await self.cmd('rehearsal_tick')
            self.assertEqual(seconds_remaining(self.host._rehearsal), 1)
            self.assertEqual(self.host.state()['rehearsal']['current_index'], index)
            self.clocks.advance(1)
            await self.cmd('rehearsal_tick')
            if index < 2:
                self.clocks.advance(7200)
                await self.cmd('rehearsal_tick')
                self.assertEqual(self.host.state()['rehearsal']['current_index'], index + 1)
                await self.model()
        state = self.host.state()['rehearsal']
        self.assertEqual(state['status'], 'COMPLETE')
        self.assertEqual([q['elapsed_seconds'] for q in state['timing']['questions']], [900,900,900])
        self.assertEqual(state['timing']['elapsed_seconds'], 2700)
        await self.reopen()
        self.assertEqual(self.host.state()['rehearsal']['status'], 'COMPLETE')

    async def test_late_model_reply_cannot_enter_the_next_question(self):
        await self.start()
        prepared = (await self.cmd('native_prepare_preview', {
            'request_id': 'pending', 'generation': 'generation', 'operation': 'reply',
            'kind': 'plan', 'text': 'Candidate reasoning', 'mechanism': 'STRICT_CHALLENGING'}))['prepared']
        self.clocks.advance(950)
        response = await self.cmd('native_commit_preview', {
            'transaction_id': prepared['transaction_id'], 'request_id': 'pending', 'generation': 'generation',
            'reply': {'reply': 'Late answer'}, 'model': 'mock', 'usage': None}, expected=False)
        self.assertEqual(response['error'], 'REHEARSAL_QUESTION_TIME_LIMIT')
        state = response['state']['rehearsal']
        self.assertEqual(state['current_index'], 1)
        self.assertEqual(state['results'][0]['time_metrics']['elapsed_seconds'], 900)
        self.assertEqual(state['results'][0]['time_metrics']['model_wait_seconds'], 900)
        self.assertEqual(sum(e['actor'] == 'interviewer' for e in state['results'][0]['session']['events']), 1)
        self.assertEqual(state['results'][0]['outcome'], 'TIMED_OUT')
        await self.reopen()
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 1)

    async def test_cancel_and_invalid_provider_reply_leave_question_open(self):
        await self.start()
        prepared = (await self.cmd('native_prepare_preview', {
            'request_id': 'cancelled', 'generation': 'generation', 'operation': 'reply',
            'kind': 'clarify', 'text': 'Candidate asks about null handling.',
            'mechanism': 'STRICT_CHALLENGING'}))['prepared']
        await self.cmd('native_commit_preview', {
            'transaction_id': prepared['transaction_id'], 'request_id': 'cancelled', 'generation': 'generation',
            'reply': {'reply': ''}, 'model': 'mock', 'usage': None}, expected=False)
        await self.cmd('native_cancel_preview')
        state = self.host.state()
        self.assertEqual(state['rehearsal']['status'], 'ACTIVE')
        self.assertEqual(state['rehearsal']['current_index'], 0)
        self.assertEqual(state['rehearsal']['results'], [])
        self.assertTrue(state['live_preview']['can_send'])
        self.assertEqual(state['live_preview']['retry_input']['text'], 'Candidate asks about null handling.')
        await self.reopen()
        self.assertEqual(self.host.state()['rehearsal']['results'], [])

    async def test_clock_integrity_hold_does_not_close_or_advance(self):
        await self.start()
        self.clocks.wall -= 20
        await self.cmd('rehearsal_tick')
        state = self.host.state()
        self.assertEqual(state['rehearsal']['status'], 'ACTIVE')
        self.assertEqual(state['rehearsal']['current_index'], 0)
        self.assertEqual(state['rehearsal']['results'], [])
        self.assertEqual(state['live_preview']['session']['phase'], 'INTERVIEWING')
        self.assertEqual(state['rehearsal']['timing']['integrity'], 'WALL_ROLLBACK_HOLD')
        await self.cmd('rehearsal_skip')
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 1)

    async def test_late_sql_execution_is_not_counted_and_cannot_affect_next_question(self):
        await self.start()
        await self.model('reply', 'implement', legacy_grading.SQL)
        qhash = self.host.state()['rehearsal']['questions'][0]['content_sha256']
        review = (await self.cmd('grade_inspect', {
            'fixture_json': legacy_grading.fixture(qhash)}))['state']['grading_review']
        def delayed(*args, **kwargs):
            self.clocks.advance(901)
            return legacy_grading.witnessed_review(review)
        with patch('tia_runtime.app_host.find_approved_pg_config', return_value='/fake/pg_config'), \
             patch('tia_runtime.app_host.grade_fixture', side_effect=delayed):
            state = (await self.cmd('grade_execute', {'fixture_sha256': review['fixture_sha256']}))['state']
        self.assertEqual(state['rehearsal']['status'], 'ACTIVE')
        self.assertEqual(state['rehearsal']['current_index'], 1)
        self.assertEqual(state['rehearsal']['results'][0]['outcome'], 'TIMED_OUT')
        self.assertNotIn('sql_accuracy', state['rehearsal']['results'][0])
        self.assertEqual(state['rehearsal']['execution'], 'NOT_RUN')
        with patch('tia_runtime.app_host.grade_fixture', side_effect=AssertionError('SQL replay forbidden')):
            await self.reopen()
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 1)
        self.assertEqual(self.host.state()['rehearsal']['execution'], 'NOT_RUN')

    async def test_skip_introduction_is_dialogue_not_skip_question(self):
        await self.start()
        prepared, response = await self.model('reply', 'clarify',
            'Skip the introduction and read the question please.',
            answer='The public task is to compute a distinct keyed rollup.')
        self.assertIn('CONTINUOUS QUESTION POLICY tia-continuity/v3', prepared['instructions'])
        self.assertIn('not as Skip Question or Final Submit', prepared['instructions'])
        self.assertEqual(response['state']['rehearsal']['current_index'], 0)
        self.assertEqual(response['state']['rehearsal']['results'], [])
        self.assertEqual(response['state']['live_preview']['candidate_turns_used'], 1)
        await self.reopen()
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 0)

    async def test_storage_preflight_is_explicit_and_does_not_close_question(self):
        await self.start()
        with patch('tia_runtime.app_host.MAX_SAVE_BYTES', 100):
            response = await self.cmd('native_prepare_preview', {
                'request_id': 'storage', 'generation': 'generation', 'operation': 'reply',
                'kind': 'clarify', 'text': 'Not sent', 'mechanism': 'STRICT_CHALLENGING'}, expected=False)
        self.assertEqual(response['error'], 'LOCAL_STORAGE_LIMIT')
        self.assertEqual(response['state']['rehearsal']['status'], 'ACTIVE')
        self.assertEqual(response['state']['rehearsal']['results'], [])
        self.assertEqual(response['state']['live_preview']['candidate_turns_used'], 0)
        self.assertFalse(response['state']['live_preview']['pending'])
        await self.cmd('rehearsal_skip')
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 1)

    async def test_code_then_clarification_can_finalize_latest_submission(self):
        await self.start()
        await self.model('reply', 'implement', 'SELECT 1;')
        await self.model('reply', 'clarify', 'That is my final code; it excludes NULL dates.')
        await self.cmd('rehearsal_submit')
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 1)
        self.assertEqual(self.host.state()['rehearsal']['results'][0]['outcome'], 'SUBMITTED_UNVERIFIED')
        await self.reopen()
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 1)

    async def test_pre_p0_v2_native_journal_replays_exact_stored_digest(self):
        # Captured before P0 from mock HTTP WebKit automation, never user data.
        # This frozen source is an independent replay oracle, not recomputed here.
        fixture = Path(__file__).parent / 'fixtures/continuity_v2_pre_p0_synthetic.json'
        document = json.loads(fixture.read_text())
        self.clocks.wall = document['journal'][-1]['wall_seconds']
        with patch('tia_runtime.app_host.grade_fixture', side_effect=AssertionError('SQL replay forbidden')):
            await self.host._restore(document)
        self.assertEqual(self.host._state_digest(), document['state_sha256'])
        self.assertEqual(self.host.state()['rehearsal']['continuity_policy'], 'tia-continuity/v2')
        self.assertEqual(self.host.state()['rehearsal']['status'], 'COMPLETE')
        self.assertEqual(self.host._journal, document['journal'])

    async def test_legacy_v2_keeps_last_implement_final_submission_rule(self):
        await self.setup_three()
        await self.cmd('rehearsal_start', {'continuity_policy': 'tia-continuity/v2'})
        await self.model()
        self.assertEqual(self.host._live_controller.config.max_events, 128)
        await self.model('reply', 'implement', 'SELECT 1;')
        await self.model('reply', 'clarify', 'Please repeat that explanation.')
        response = await self.cmd('rehearsal_submit', expected=False)
        self.assertEqual(response['error'], 'FINAL_CODE_SUBMISSION_REQUIRED')
        await self.reopen()
        self.assertEqual(self.host.state()['rehearsal']['current_index'], 0)

    async def test_completed_export_does_not_claim_zero_native_requests(self):
        await self.start()
        for _ in range(3):
            await self.cmd('rehearsal_skip')
        self.assertIsNone(self.host._live_controller)
        before = self.host._state_digest()
        exported = self.host.export()
        self.assertIsNone(exported['api_requests'])
        self.assertIn('complete session request count unavailable', exported['provider_usage_source'])
        self.assertEqual(self.host._state_digest(), before)
        self.assertNotIn('native_provider_at_export', exported)
        await self.reopen()
        self.assertIsNone(self.host.export()['api_requests'])

    async def test_invalid_policy_cannot_change_legacy_semantics(self):
        await self.setup_three()
        response = await self.cmd('rehearsal_start', {'continuity_policy': 'tia-continuity/v999'}, expected=False)
        self.assertEqual(response['error'], 'INVALID_CONTINUITY_POLICY')
        await self.cmd('rehearsal_start')
        await self.model()
        for turn in range(4):
            await self.model('reply', 'clarify', f'Legacy event {turn}')
        self.assertFalse(self.host.state()['live_preview']['can_send'])
        self.assertEqual(self.host.state()['live_preview']['candidate_turn_limit'], 4)
        await self.reopen()
        self.assertFalse(self.host.state()['live_preview']['can_send'])


if __name__ == '__main__':
    unittest.main()
