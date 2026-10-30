"""Frozen prior-release journal recovery; synthetic text and no provider calls."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tia_runtime import native_evaluator as ev
from tia_runtime import post_interview_sql as post_sql
from tia_runtime.app_host import TutorialHost, HostError, digest
from tia_runtime.persistence import TutorialStore
import test_p0_continuity as continuity


FIXTURE = Path(__file__).parent / 'fixtures' / 'evaluator_p0_v3_journal_golden.json'


class EvaluatorProtocolReplayTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = continuity.ContinuityV3Tests.asyncSetUp
    asyncTearDown = continuity.ContinuityV3Tests.asyncTearDown
    cmd = continuity.ContinuityV3Tests.cmd
    setup_three = continuity.ContinuityV3Tests.setup_three
    model = continuity.ContinuityV3Tests.model
    start = continuity.ContinuityV3Tests.start

    async def restore_document(self, document):
        self.host.close()
        store = TutorialStore(self.directory.name)
        store.write(document)
        store.close()
        with patch('subprocess.Popen', side_effect=AssertionError('No process during replay')), \
             patch('socket.create_connection', side_effect=AssertionError('No network during replay')):
            self.host = await TutorialHost.open(self.directory.name,
                clock=lambda: self.clocks.monotonic, wall_clock=lambda: self.clocks.wall)
        return self.host.state()

    async def finish_synthetic_interview(self):
        await self.start()
        await self.model('reply', 'implement', 'SELECT 1;')
        await self.cmd('rehearsal_submit')
        await self.cmd('rehearsal_skip')
        await self.cmd('rehearsal_skip')

    async def evaluate(self):
        spec = (await self.cmd('native_prepare_evaluator', {
            'request_id': 'current-evaluator', 'generation': 'current-generation', 'question_index': 0}))['prepared']
        proposal = {'assessments': [[key, None, [], 'Insufficient evidence for this criterion.'] for key in ev.IDS]}
        await self.cmd('native_commit_evaluator', {
            'transaction_id': spec['transaction_id'], 'request_id': spec['request_id'],
            'generation': spec['generation'], 'reply': {'reply': json.dumps(proposal, separators=(',', ':'))},
            'model': 'synthetic-current-evaluator', 'usage': None})
        return spec

    async def test_shipped_v3_journal_restores_original_artifact_without_reexecution(self):
        fixture = json.loads(FIXTURE.read_text())
        self.assertEqual(fixture['assessment']['sha256'],
                         '0ddb9361c4fab0eb7a9019bcca77bf3294b0d76d4cfa51e6dd74e3481a1e0c93')
        state = await self.restore_document(fixture['completed_document'])
        self.assertIsNone(state['recovery_error'])
        self.assertEqual(state['screen'], 'REHEARSAL_COMPLETE')
        self.assertEqual(self.host._journal, fixture['completed_document']['journal'])
        self.assertEqual(self.host._evaluator_assessments['0'], fixture['assessment'])
        view = state['evaluator_report']['questions'][0]['assessment']
        self.assertEqual(view['status'], 'LEGACY_CONTEXT_REVIEW_REQUIRED')
        self.assertEqual(view['sha256'], fixture['assessment']['sha256'])
        self.assertEqual(view['dimensions'], fixture['assessment']['dimensions'])

    async def test_shipped_pending_request_is_cancelled_without_retry(self):
        original = json.loads(FIXTURE.read_text())['pending_document']
        state = await self.restore_document(original)
        self.assertIsNone(state['recovery_error'])
        self.assertFalse(state['native_evaluator_pending'])
        self.assertTrue(state['native_evaluator_interrupted'])
        self.assertEqual(self.host._journal[:-1], original['journal'])
        self.assertEqual(self.host._journal[-1]['action'], 'native_cancel_evaluator')

    async def test_new_request_marks_protocol_and_replays_exact_artifact(self):
        await self.finish_synthetic_interview()
        spec = await self.evaluate()
        original = copy.deepcopy(self.host._evaluator_assessments['0'])
        document = self.host.store.read()
        prepare = [e for e in document['journal'] if e['action'] == 'native_prepare_evaluator'][-1]
        self.assertEqual(prepare['evaluator_protocol_version'], ev.STRUCTURED_REPLY_CONTRACT)
        self.assertEqual(json.loads(spec['input'])['response_contract'], ev.STRUCTURED_REPLY_CONTRACT)
        state = await self.restore_document(document)
        self.assertIsNone(state['recovery_error'])
        self.assertEqual(self.host._evaluator_assessments['0'], original)

    async def test_unknown_protocol_or_downgrade_cannot_relabel_transactions(self):
        await self.finish_synthetic_interview()
        await self.evaluate()
        current = self.host.store.read()
        for version in ('invented-version', None):
            document = copy.deepcopy(current)
            prepare = [e for e in document['journal'] if e['action'] == 'native_prepare_evaluator'][-1]
            if version is None:
                prepare.pop('evaluator_protocol_version')
            else:
                prepare['evaluator_protocol_version'] = version
            document['document_sha256'] = digest({k: v for k, v in document.items() if k != 'document_sha256'})
            state = await self.restore_document(document)
            self.assertEqual(state['recovery_error'], 'INVALID_SAVE')

    async def test_old_commit_cannot_be_replayed_as_new_protocol(self):
        document = json.loads(FIXTURE.read_text())['completed_document']
        prepare = [e for e in document['journal'] if e['action'] == 'native_prepare_evaluator'][-1]
        prepare['evaluator_protocol_version'] = ev.STRUCTURED_REPLY_CONTRACT
        document['document_sha256'] = digest({k: v for k, v in document.items() if k != 'document_sha256'})
        self.assertEqual((await self.restore_document(document))['recovery_error'], 'INVALID_SAVE')

    async def test_protocol_is_not_a_renderer_or_native_command_parameter(self):
        with self.assertRaisesRegex(HostError, 'INVALID_COMMAND'):
            await self.host.command('native_prepare_evaluator', {
                'request_id': 'no-downgrade', 'generation': 'generation', 'question_index': 0,
                'replay_protocol': ev.LEGACY_REPLY_PROTOCOL})

    async def test_old_assessment_survives_post_sql_archive_and_current_reevaluation(self):
        fixture = json.loads(FIXTURE.read_text())
        self.assertIsNone((await self.restore_document(fixture['completed_document']))['recovery_error'])
        await self.cmd('post_sql_review', {'question_index': 0, 'suite_id': 'bus_last_person'})
        review = self.host.state()['post_interview_sql']['review']
        packet = (await self.cmd('native_prepare_post_sql', {
            'request_id': 'local-cases', 'generation': 'local-generation',
            'review_sha256': review['review_sha256']}))['prepared']
        def synthetic_runner(*args, **kwargs):
            return {'result': {'status': 'PASSED', 'reason': 'PASS'}}
        result = post_sql.execute(packet, runner=synthetic_runner, pg_config='synthetic')
        await self.cmd('native_commit_post_sql', {'result': result})
        self.assertEqual(self.host._evaluator_archive[0]['assessment'], fixture['assessment'])
        spec = await self.evaluate()
        self.assertEqual(json.loads(spec['input'])['local_execution']['execution_time'], 'AFTER_INTERVIEW')
        original = copy.deepcopy(self.host._evaluator_assessments['0'])
        state = await self.restore_document(self.host.store.read())
        self.assertIsNone(state['recovery_error'])
        self.assertEqual(self.host._evaluator_archive[0]['assessment'], fixture['assessment'])
        self.assertEqual(self.host._evaluator_assessments['0'], original)


if __name__ == '__main__':
    unittest.main()
