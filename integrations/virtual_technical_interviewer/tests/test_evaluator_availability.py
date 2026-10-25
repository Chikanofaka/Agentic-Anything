"""Optional evaluator-source failures never disable unrelated frozen interview data."""
import unittest
from unittest.mock import patch

from tia_runtime.app_host import TutorialHost
from tia_runtime.native_evaluator import NativeEvaluatorError
import test_evaluator_host as evaluator_host


class EvaluatorAvailabilityTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = evaluator_host.EvaluatorHostTests.asyncSetUp
    asyncTearDown = evaluator_host.EvaluatorHostTests.asyncTearDown
    cmd = evaluator_host.EvaluatorHostTests.cmd
    inspected = evaluator_host.EvaluatorHostTests.inspected
    grade = evaluator_host.EvaluatorHostTests.grade
    configure_sql = evaluator_host.EvaluatorHostTests.configure_sql
    start = evaluator_host.EvaluatorHostTests.start
    model = evaluator_host.EvaluatorHostTests.model
    setup_three = evaluator_host.EvaluatorHostTests.setup_three
    closed = evaluator_host.EvaluatorHostTests.closed

    def source_failure(self):
        return patch('tia_runtime.native_evaluator.compile_evaluator_profile',
                     side_effect=NativeEvaluatorError('EVALUATOR_PROFILE_INVALID'))

    async def test_source_drift_keeps_active_snapshot_and_export_available(self):
        await self.inspected()
        old = self.host.state()
        old_digest = self.host._state_digest()
        with self.source_failure():
            response = await self.host.handle({'id': 'snapshot-test', 'action': 'snapshot', 'params': {}})
            self.assertTrue(response['ok'])
            self.assertEqual(response['state']['evaluator_report']['status'], 'UNAVAILABLE')
            self.assertEqual(response['state']['rehearsal'], old['rehearsal'])
            self.assertEqual(response['state']['evidence_scorecard'], old['evidence_scorecard'])
            self.assertEqual(self.host._state_digest(), old_digest)
            exported = await self.host.handle({'id': 'export-test', 'action': 'export', 'params': {}})
            self.assertTrue(exported['ok'])
            self.assertEqual(exported['export']['evaluator_report']['status'], 'UNAVAILABLE')
            self.assertEqual(exported['export']['rehearsal'], old['rehearsal'])

    async def test_active_legacy_journal_reopens_with_source_failure(self):
        await self.inspected()
        results = self.host.state()['rehearsal']['results']
        self.host.close()
        with self.source_failure():
            self.host = await TutorialHost.open(self.directory.name)
            state = self.host.state()
            self.assertIsNone(state['recovery_error'])
            self.assertEqual(state['evaluator_report']['status'], 'UNAVAILABLE')
            self.assertEqual(state['rehearsal']['results'], results)
            self.assertEqual(state['rehearsal']['status'], 'ACTIVE')

    async def test_closed_legacy_journal_reopens_and_exports_with_source_failure(self):
        await self.closed(verified=True)
        old = self.host.state()
        self.host.close()
        with self.source_failure():
            self.host = await TutorialHost.open(self.directory.name)
            state = self.host.state()
            self.assertIsNone(state['recovery_error'])
            self.assertEqual(state['rehearsal'], old['rehearsal'])
            self.assertEqual(state['evidence_scorecard'], old['evidence_scorecard'])
            self.assertEqual(self.host.export()['rehearsal'], old['rehearsal'])
            self.assertEqual(self.host.export()['evaluator_report']['status'], 'UNAVAILABLE')

    async def test_source_failure_prevents_paid_preparation_and_never_creates_pending(self):
        await self.closed()
        with self.source_failure():
            response = await self.host.handle({'id': 'evaluator-test', 'action': 'native_prepare_evaluator',
                'params': {'question_index': 0, 'request_id': 'req-1', 'generation': 'gen-1'}})
            self.assertFalse(response['ok'])
            self.assertEqual(response['error'], 'EVALUATOR_PROFILE_INVALID')
            self.assertNotIn('prepared', response)
            self.assertFalse(response['state']['native_evaluator_pending'])
            self.assertEqual(response['state']['evaluator_report']['status'], 'UNAVAILABLE')
            self.assertEqual(self.host._evaluator_assessments, {})

    async def test_source_failure_after_prepare_rejects_commit_but_allows_cancellation(self):
        await self.closed()
        response = await self.cmd('native_prepare_evaluator', {
            'question_index': 0, 'request_id': 'req-1', 'generation': 'gen-1'})
        params = evaluator_host.commitment(response['prepared'])
        with self.source_failure():
            response = await self.host.handle({'id': 'evaluator-commit', 'action': 'native_commit_evaluator', 'params': params})
            self.assertFalse(response['ok'])
            self.assertEqual(response['error'], 'EVALUATOR_SOURCE_CHANGED')
            self.assertTrue(response['state']['native_evaluator_pending'])
            self.assertEqual(self.host._evaluator_assessments, {})
            cancelled = await self.host.handle({'id': 'evaluator-cancel', 'action': 'native_cancel_evaluator', 'params': {}})
            self.assertTrue(cancelled['ok'])
            self.assertFalse(cancelled['state']['native_evaluator_pending'])
            self.assertTrue(cancelled['state']['native_evaluator_interrupted'])


if __name__ == '__main__':
    unittest.main()
