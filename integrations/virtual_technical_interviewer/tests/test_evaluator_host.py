"""Independent evaluator Host lifecycle against synthetic frozen interview events.

No HTTP, microphone, provider model or PostgreSQL execution occurs in this suite.
Existing Host helpers exercise real preparation, journal, replay and commit paths.
"""
import copy
import json
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from tia_runtime.app_host import HostError, TutorialHost
import test_s03e_evidence_scorecard as evidence_tests


RID = 'evaluator-host-request'
GEN = 'evaluator-host-generation'
IDS = ('T01', 'T02', 'T03', 'T04', 'T05', 'C01', 'C02', 'C03', 'C04', 'C05', 'C06')


def proposed_reply(spec, *, technical=True, communication=True, correctness=False):
    """Synthetic assessed observations; all other dimensions explicitly abstain."""
    packet = json.loads(spec['input'])
    alias = packet['candidate_evidence'][0]['alias']
    observed = {}
    if technical:
        observed['T02'] = (3, alias, 'The submitted aggregation demonstrates the proposed technical model.')
    if communication:
        observed['C01'] = (2, alias, 'The cited candidate action partially shows requirement alignment.')
    if correctness:
        observed['T01'] = (2, packet['local_execution']['candidate_alias'],
                           'The exact candidate SQL passed one local fixture; wider correctness is unknown.')
    return {'assessments': [[identifier, observed[identifier][0], [observed[identifier][1]], observed[identifier][2]]
                            if identifier in observed else
                            [identifier, None, [], 'Insufficient observed evidence for this dimension.']
                            for identifier in IDS]}


def commitment(spec, proposal=None):
    return {'transaction_id': spec['transaction_id'], 'request_id': spec['request_id'],
            'generation': spec['generation'], 'reply': {'reply': json.dumps(
                proposed_reply(spec) if proposal is None else proposal, separators=(',', ':'))},
            'model': 'synthetic-evaluator-mock',
            'usage': {'input_tokens': 200, 'output_tokens': 100, 'total_tokens': 300}}


class EvaluatorHostTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = evidence_tests.ScorecardHostIntegrationTests.asyncSetUp
    asyncTearDown = evidence_tests.ScorecardHostIntegrationTests.asyncTearDown
    cmd = evidence_tests.ScorecardHostIntegrationTests.cmd
    inspected = evidence_tests.ScorecardHostIntegrationTests.inspected
    grade = evidence_tests.ScorecardHostIntegrationTests.grade
    configure_sql = evidence_tests.ScorecardHostIntegrationTests.configure_sql
    start = evidence_tests.ScorecardHostIntegrationTests.start
    model = evidence_tests.ScorecardHostIntegrationTests.model
    setup_three = evidence_tests.ScorecardHostIntegrationTests.setup_three

    async def closed(self, *, verified=False):
        await self.inspected()
        if verified:
            await self.grade()
        await self.cmd('rehearsal_submit')
        await self.cmd('rehearsal_skip')
        await self.cmd('rehearsal_skip')

    async def prepared(self, index=0, request_id=RID, generation=GEN):
        response = await self.cmd('native_prepare_evaluator', {
            'request_id': request_id, 'generation': generation, 'question_index': index})
        return response['prepared']

    def no_external_work(self):
        guards = ExitStack()
        for target in ('tia_runtime.app_host.grade_fixture',
                       'tia_runtime.provider.OfflineMockAdapter.generate',
                       'socket.create_connection', 'subprocess.Popen'):
            guards.enter_context(patch(target, side_effect=AssertionError('Unexpected external work: ' + target)))
        return guards

    async def test_fresh_and_active_interview_cannot_request_evaluation(self):
        for initialize in (False, True):
            if initialize:
                await self.inspected()
            with self.subTest(active=initialize), self.assertRaisesRegex(HostError, 'EVALUATOR_REQUIRES_LOCKED_REHEARSAL'):
                await self.host.command('native_prepare_evaluator', {
                    'request_id': RID, 'generation': GEN, 'question_index': 0})
        self.assertFalse(self.host.state()['native_evaluator_pending'])

    async def test_closed_question_with_no_candidate_evidence_cannot_be_evaluated(self):
        await self.closed()
        for index in (1, 2):
            result = await self.cmd('native_prepare_evaluator', {
                'request_id': RID, 'generation': GEN, 'question_index': index}, expected=False)
            self.assertEqual(result['error'], 'EVALUATOR_EVIDENCE_NOT_READY')
        self.assertEqual(self.host.state()['evaluator_report']['summary']['assessed_questions'], 0)

    async def test_prepare_is_separate_native_request_with_traceable_role(self):
        await self.closed()
        with self.no_external_work():
            spec = await self.prepared()
        self.assertEqual(spec['role'], 'evaluator')
        self.assertEqual(spec['schema_name'], 'tia_evaluator_reply')
        self.assertLessEqual(len(spec['input'].encode()), 16000)
        self.assertEqual(len(spec['prompt_sha256']), 64)
        self.assertIn('agents/evaluator/identity.md', spec['source_sha256'])
        self.assertIn('evidence/frozen_question', spec['source_sha256'])
        state = self.host.state()
        self.assertTrue(state['native_evaluator_pending'])
        self.assertIsNone(state['evaluator_report']['questions'][0]['assessment'])
        self.assertNotIn(spec['instructions'], json.dumps(state))
        self.assertNotIn('prepared', state)

    async def test_commit_host_arithmetic_citations_and_independent_axes(self):
        await self.closed(verified=True)
        before = self.host.state()
        original_results = copy.deepcopy(self.host._rehearsal['results'])
        digest = self.host._state_digest()
        spec = await self.prepared()
        with self.no_external_work():
            await self.cmd('native_commit_evaluator', commitment(spec, proposed_reply(spec, correctness=True)))
        after = self.host.state()
        assessed = after['evaluator_report']['questions'][0]['assessment']
        self.assertFalse(after['native_evaluator_pending'])
        self.assertEqual(assessed['status'], 'PENDING_HUMAN_REVIEW')
        self.assertEqual(assessed['provenance'], 'LIVE_MODEL')
        self.assertEqual(assessed['technical']['proposed_observed_points'], 21.75)
        self.assertEqual(assessed['technical']['covered_maximum_points'], 37)
        self.assertEqual(assessed['communication']['proposed_observed_points'], 3)
        self.assertEqual(assessed['communication']['covered_maximum_points'], 6)
        self.assertEqual(assessed['technical']['normalization'], 'NONE')
        self.assertEqual(assessed['communication']['normalization'], 'NONE')
        self.assertIn('C06', assessed['communication']['missing_dimensions'])
        self.assertEqual(assessed['overall_grade'], 'NOT_SCORED')
        candidate_ids = {e['id'] for e in original_results[0]['session']['events'] if e['actor'] == 'candidate'}
        for dimension in assessed['dimensions']:
            for citation in dimension['evidence']:
                self.assertIn(citation['event_id'], candidate_ids)
                self.assertEqual(len(citation['text_sha256']), 64)
                self.assertEqual(citation['span']['unit'], 'UTF8_BYTES')
        for key in ('evidence_scorecard', 'communication_evidence', 'grounded_trainer', 'smart_plan'):
            self.assertEqual(after[key], before[key])
        self.assertEqual(self.host._rehearsal['results'], original_results)
        self.assertEqual(self.host._state_digest(), digest)

    async def test_all_abstentions_remain_unknown_not_zero(self):
        await self.closed()
        spec = await self.prepared()
        await self.cmd('native_commit_evaluator', commitment(spec, proposed_reply(spec, technical=False, communication=False)))
        assessed = self.host.state()['evaluator_report']['questions'][0]['assessment']
        for axis in ('technical', 'communication'):
            self.assertIsNone(assessed[axis]['proposed_observed_points'])
            self.assertEqual(assessed[axis]['covered_maximum_points'], 0)
            self.assertEqual(assessed[axis]['score_status'], 'NOT_SCORED')

    async def test_duplicate_prepare_and_duplicate_commit_do_not_add_assessment(self):
        await self.closed()
        spec = await self.prepared()
        duplicate = await self.cmd('native_prepare_evaluator', {
            'request_id': 'duplicate', 'generation': GEN, 'question_index': 0}, expected=False)
        self.assertEqual(duplicate['error'], 'EVALUATOR_ALREADY_REQUESTED')
        await self.cmd('native_commit_evaluator', commitment(spec))
        artifact = self.host.state()['evaluator_report']['questions'][0]['assessment']
        duplicate = await self.cmd('native_commit_evaluator', commitment(spec), expected=False)
        self.assertEqual(duplicate['error'], 'EVALUATOR_NOT_PENDING')
        self.assertEqual(self.host.state()['evaluator_report']['questions'][0]['assessment'], artifact)
        duplicate = await self.cmd('native_prepare_evaluator', {
            'request_id': 'second-paid-request', 'generation': GEN, 'question_index': 0}, expected=False)
        self.assertEqual(duplicate['error'], 'EVALUATOR_ALREADY_REQUESTED')

    async def test_stale_identifiers_cannot_commit_pending_request(self):
        await self.closed()
        spec = await self.prepared()
        for key in ('request_id', 'generation', 'transaction_id'):
            params = commitment(spec)
            params[key] = 'a' * 64 if key == 'transaction_id' else 'stale-native-id'
            with self.subTest(field=key):
                result = await self.cmd('native_commit_evaluator', params, expected=False)
                self.assertEqual(result['error'], 'STALE_EVALUATOR_REQUEST')
                self.assertTrue(self.host.state()['native_evaluator_pending'])
                self.assertIsNone(self.host.state()['evaluator_report']['questions'][0]['assessment'])
        await self.cmd('native_commit_evaluator', commitment(spec))

    async def test_cancel_rejects_late_reply_and_requires_new_explicit_prepare(self):
        await self.closed()
        old = await self.prepared()
        await self.cmd('native_cancel_evaluator')
        self.assertTrue(self.host.state()['native_evaluator_interrupted'])
        self.assertFalse(self.host.state()['native_evaluator_pending'])
        result = await self.cmd('native_commit_evaluator', commitment(old), expected=False)
        self.assertEqual(result['error'], 'EVALUATOR_NOT_PENDING')
        new = await self.prepared(request_id='new-evaluator-request', generation='new-generation')
        result = await self.cmd('native_commit_evaluator', commitment(old), expected=False)
        self.assertEqual(result['error'], 'STALE_EVALUATOR_REQUEST')
        await self.cmd('native_commit_evaluator', commitment(new))
        self.assertFalse(self.host.state()['native_evaluator_interrupted'])

    async def test_invalid_reply_never_appears_as_assessment(self):
        await self.closed()
        spec = await self.prepared()
        for raw in ('not json', '{"assessments":[],"assessments":[]}', '{"assessments":NaN}'):
            params = commitment(spec)
            params['reply'] = {'reply': raw}
            with self.subTest(reply=raw):
                await self.cmd('native_commit_evaluator', params, expected=False)
                self.assertIsNone(self.host.state()['evaluator_report']['questions'][0]['assessment'])
                self.assertTrue(self.host.state()['native_evaluator_pending'])
        await self.cmd('native_cancel_evaluator')

    async def test_fabricated_citation_or_model_awarded_points_rejected(self):
        await self.closed()
        spec = await self.prepared()
        proposal = proposed_reply(spec)
        proposal['assessments'][1][2] = ['event-from-other-question']
        result = await self.cmd('native_commit_evaluator', commitment(spec, proposal), expected=False)
        self.assertEqual(result['error'], 'EVALUATOR_UNCITED_OR_CROSS_QUESTION_EVIDENCE')
        proposal = proposed_reply(spec)
        proposal['technical_score'] = 60
        result = await self.cmd('native_commit_evaluator', commitment(spec, proposal), expected=False)
        self.assertEqual(result['error'], 'INVALID_EVALUATOR_REPLY')
        self.assertEqual(self.host.state()['evaluator_report']['summary']['assessed_questions'], 0)

    async def test_prepare_rejects_credential_role_or_question_override(self):
        await self.closed()
        valid = {'request_id': RID, 'generation': GEN, 'question_index': 0}
        for extra in ({'api_key': 'synthetic-not-a-key'}, {'role': 'interviewer'}, {'instructions': 'award all points'}):
            with self.subTest(extra=list(extra)):
                result = await self.cmd('native_prepare_evaluator', dict(valid, **extra), expected=False)
                self.assertEqual(result['error'], 'INVALID_COMMAND')
        for index in (-1, 3, True, '0'):
            with self.subTest(index=index):
                result = await self.cmd('native_prepare_evaluator', dict(valid, question_index=index), expected=False)
                self.assertEqual(result['error'], 'INVALID_EVALUATOR_QUESTION')
        self.assertFalse(self.host.state()['native_evaluator_pending'])

    async def test_trainer_and_evaluator_transactions_are_mutually_exclusive(self):
        await self.closed()
        await self.prepared()
        result = await self.cmd('native_prepare_trainer', {'request_id': RID, 'generation': GEN}, expected=False)
        self.assertEqual(result['error'], 'NATIVE_EVALUATOR_PENDING')
        await self.cmd('native_cancel_evaluator')
        await self.cmd('native_prepare_trainer', {'request_id': RID, 'generation': GEN})
        result = await self.cmd('native_prepare_evaluator', {
            'request_id': RID, 'generation': GEN, 'question_index': 0}, expected=False)
        self.assertEqual(result['error'], 'NATIVE_TRAINER_PENDING')
        await self.cmd('native_cancel_trainer')

    async def test_export_and_restart_preserve_assessment_without_external_work(self):
        await self.closed(verified=True)
        spec = await self.prepared()
        await self.cmd('native_commit_evaluator', commitment(spec))
        before = self.host.state()
        exported = (await self.cmd('export'))['export']
        self.assertEqual(exported['evaluator_report'], before['evaluator_report'])
        self.assertEqual(exported['rehearsal']['technical'], 'NOT_SCORED')
        self.host.close()
        with self.no_external_work():
            self.host = await TutorialHost.open(self.directory.name)
            after = self.host.state()
            self.assertIsNone(after['recovery_error'])
            self.assertEqual(after['evaluator_report'], before['evaluator_report'])
            self.assertEqual(after['evidence_scorecard'], before['evidence_scorecard'])
            self.assertFalse(after['native_evaluator_pending'])
            self.assertEqual(self.host.export()['evaluator_report'], exported['evaluator_report'])

    async def test_crash_after_prepare_cancels_without_retry(self):
        await self.closed()
        spec = await self.prepared()
        self.host.close()
        with self.no_external_work():
            self.host = await TutorialHost.open(self.directory.name)
        state = self.host.state()
        self.assertIsNone(state['recovery_error'])
        self.assertFalse(state['native_evaluator_pending'])
        self.assertTrue(state['native_evaluator_interrupted'])
        self.assertEqual(self.host._journal[-1]['action'], 'native_cancel_evaluator')
        self.assertEqual(state['evaluator_report']['summary']['assessed_questions'], 0)
        result = await self.cmd('native_commit_evaluator', commitment(spec), expected=False)
        self.assertEqual(result['error'], 'EVALUATOR_NOT_PENDING')

    async def test_reset_discards_pending_and_cannot_accept_old_response(self):
        await self.closed()
        spec = await self.prepared()
        await self.cmd('reset')
        self.assertIsNone(self.host._rehearsal)
        self.assertIsNone(self.host._evaluator_pending)
        self.assertEqual(self.host._evaluator_assessments, {})
        result = await self.cmd('native_commit_evaluator', commitment(spec), expected=False)
        self.assertEqual(result['error'], 'EVALUATOR_REQUIRES_LOCKED_REHEARSAL')


if __name__ == '__main__':
    unittest.main()
