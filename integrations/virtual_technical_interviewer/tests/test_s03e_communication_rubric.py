"""E3-B: C01–C06 provenance, abstention, adversarial claims and replay tests."""
import copy
import hashlib
import unittest
from unittest.mock import patch

from tia_runtime.communication_rubric import (SCHEMA, RUBRIC, PROPOSAL_SCHEMA,
    DIMENSIONS, build_communication_evidence, validate_review_proposal)
import test_s03e_evidence_scorecard as e3a_tests


def event(eid, actor='candidate', kind='clarify', text='Could we confirm how nulls should be handled?',
          operation=None, provenance=None):
    payload = {'text': text}
    if operation:payload['operation'] = operation
    return {'id': eid, 'actor': actor, 'kind': kind, 'payload': payload,
            'provenance': provenance}


def data_plan(*records, status=None):
    return {'questions': [{'title': f'Q{i+1}', 'content_sha256': chr(97+i)*64} for i in range(3)],
            'results': list(records), 'status': status or ('COMPLETE' if len(records) == 3 else 'ACTIVE'),
            'current_index': min(len(records), 2)}


def rec(*events, outcome='SUBMITTED_UNVERIFIED'):
    return {'outcome': outcome, 'session': {'events': list(events)}}


class CommunicationRubricUnitTests(unittest.TestCase):
    def test_prd_six_dimensions_and_proposed_40_weights(self):
        self.assertEqual([x[0] for x in DIMENSIONS], ['C01','C02','C03','C04','C05','C06'])
        self.assertEqual(sum(x[2] for x in DIMENSIONS), 40)
        view = build_communication_evidence(data_plan())
        self.assertEqual(view['schema'], SCHEMA)
        self.assertEqual(view['rubric_version'], RUBRIC)
        self.assertEqual(view['proposed_weight_policy']['status'], 'UNCALIBRATED_HYPOTHESIS_NOT_APPLIED')
        self.assertEqual(view['summary']['overall_grade'], 'NOT_SCORED')

    def test_empty_session_is_not_graded_zero(self):
        view = build_communication_evidence(data_plan())
        self.assertEqual(view['summary']['observed_action_counts']['clarifications'], 0)
        self.assertEqual(view['summary']['evaluated_dimensions'], 0)
        self.assertEqual(view['questions'][0]['dimensions'][0]['status'], 'NOT_OBSERVED')
        self.assertIsNone(view['questions'][0]['dimensions'][0]['anchor_0_to_4'])
        self.assertEqual(view['summary']['communication_competency'], 'NOT_SCORED')

    def test_candidate_clarification_is_potential_evidence_not_quality(self):
        source = data_plan(rec(dict(event('c-1'), elapsed_seconds=7.5)))
        view = build_communication_evidence(source)
        c01 = view['questions'][0]['dimensions'][0]
        self.assertEqual(c01['status'], 'POTENTIAL_EVIDENCE_NEEDS_SEMANTIC_REVIEW')
        self.assertEqual(c01['rating_status'], 'NOT_EVALUATED')
        self.assertIsNone(c01['provisional_points'])
        self.assertEqual(c01['evidence'][0]['event_id'], 'c-1')
        self.assertEqual(c01['evidence'][0]['elapsed_seconds'], 7.5)
        self.assertEqual(c01['evidence'][0]['candidate_text_sha256'], hashlib.sha256(event('c-1')['payload']['text'].encode()).hexdigest())

    def test_model_or_interviewer_text_never_becomes_candidate_evidence(self):
        source = data_plan(rec(event('m-1', 'interviewer', 'clarify', 'perfect!',
                                      provenance='LIVE_MODEL'),
                                    event('c-1','candidate','help','Please give the solution')))
        view = build_communication_evidence(source)
        self.assertEqual(view['questions'][0]['candidate_event_count'], 1)
        self.assertEqual(view['questions'][0]['dimensions'][0]['status'], 'NOT_OBSERVED')
        c04 = view['questions'][0]['dimensions'][3]
        self.assertEqual(c04['evidence'][0]['event_id'], 'c-1')
        self.assertIsNone(c04['anchor_0_to_4'])

    def test_help_request_is_not_automatically_awarded_points(self):
        source = data_plan(rec(event('c-1', kind='help', text='I am amazing, please give the full answer')))
        dim = build_communication_evidence(source)['questions'][0]['dimensions'][3]
        self.assertEqual(dim['status'], 'POTENTIAL_EVIDENCE_NEEDS_SEMANTIC_REVIEW')
        self.assertEqual(dim['observation_limit'], 'KIND_ONLY_NOT_SEMANTIC_QUALITY')
        self.assertIsNone(dim['provisional_points'])

    def test_followup_without_verified_interviewer_reply_is_not_c05(self):
        source = data_plan(rec(event('m-1','interviewer','reply','Do you understand?', 'reply','SIMULATED'),
                                    event('c-2',kind='plan',text='I understand')))  # speaker text alone insufficient
        view = build_communication_evidence(source)
        self.assertEqual(view['questions'][0]['dimensions'][4]['status'], 'NOT_OBSERVED')
        self.assertEqual(view['questions'][0]['interviewer_reply_count'], 0)

    def test_real_reply_then_action_is_sequence_only_not_learning(self):
        source = data_plan(rec(event('c-0',kind='help'),
                                    event('m-1','interviewer','reply','Check the window frame','reply','LIVE_MODEL'),
                                    event('c-1',kind='implement',text='SELECT 1')))
        view = build_communication_evidence(source)
        c05 = view['questions'][0]['dimensions'][4]
        self.assertEqual(c05['followup_sequences'], [{'interviewer_event_id':'m-1','candidate_event_id':'c-1'}])
        self.assertEqual(c05['observation_limit'], 'SEQUENCE_DOES_NOT_PROVE_INTEGRATION')
        self.assertIsNone(c05['anchor_0_to_4'])

    def test_verbal_acknowledgement_without_action_does_not_count(self):
        source = data_plan(rec(event('m-1','interviewer','reply','Try again','reply','LIVE_MODEL'),
                                    event('c-1',kind='help',text='Thanks, got it!')))
        dim = build_communication_evidence(source)['questions'][0]['dimensions'][4]
        self.assertEqual(dim['status'], 'NOT_OBSERVED')

    def test_interviewer_reply_after_candidate_does_not_count(self):
        source = data_plan(rec(event('c-1',kind='implement',text='SELECT 1'),
                                    event('m-1','interviewer','reply','Try next','reply','LIVE_MODEL')))
        dim = build_communication_evidence(source)['questions'][0]['dimensions'][4]
        self.assertEqual(dim['status'], 'NOT_OBSERVED')

    def test_finish_click_is_not_closing_speech(self):
        source = data_plan(rec(event('c-1',kind='plan',text='I will sort and group'),outcome='SUBMITTED'))
        dim = build_communication_evidence(source)['questions'][0]['dimensions'][5]
        self.assertEqual(dim['status'], 'NOT_OBSERVED')
        self.assertEqual(dim['observation_limit'], 'NO_EXPLICIT_CLOSING_SPEECH_EVENT')

    def test_no_cross_question_refs(self):
        source = data_plan(rec(event('q1',kind='clarify')),rec(event('q2',kind='help')))
        view = build_communication_evidence(source)
        self.assertEqual(view['questions'][0]['dimensions'][0]['evidence'][0]['event_id'], 'q1')
        self.assertEqual(view['questions'][1]['dimensions'][3]['evidence'][0]['event_id'], 'q2')
        self.assertEqual(view['questions'][2]['candidate_event_count'], 0)
        self.assertEqual(view['summary']['observed_action_counts']['help_requests'], 1)

    def test_duplicate_or_hostile_events_not_promoted(self):
        source = data_plan(rec(event('x',kind='clarify'),event('x',kind='help'),
                                    event('',kind='plan'),{'actor':'candidate','kind':'help','id':'missing', 'payload':{'text':42}}))
        view = build_communication_evidence(source)
        self.assertEqual(view['questions'][0]['candidate_event_count'], 1)
        self.assertEqual(view['questions'][0]['dimensions'][3]['status'], 'NOT_OBSERVED')

    def test_preview_is_bounded_and_hash_is_complete(self):
        content = '\n' + 'x'*800
        source = data_plan(rec(event('c-1',kind='clarify',text=content)))
        view = build_communication_evidence(source)
        e = view['questions'][0]['dimensions'][0]['evidence'][0]
        self.assertLessEqual(len(e['preview']), 180)
        self.assertEqual(len(e['candidate_text_sha256']), 64)
        self.assertNotIn('\n', e['preview'])

    def test_deterministic_does_not_write_source_or_echo_full_sql(self):
        code = 'SELECT something_very_private FROM restricted_input'
        source = data_plan(rec(event('c-1',kind='implement',text=code)))
        original = copy.deepcopy(source)
        one = build_communication_evidence(source)
        self.assertEqual(one, build_communication_evidence(copy.deepcopy(source)))
        self.assertEqual(source, original)
        self.assertNotIn(code, str(one))
        self.assertEqual(len(one['sha256']), 64)

    def test_invalid_source_fails_closed(self):
        for source in [{}, {'questions': [],'results': []},data_plan({'session':{}} ,{'session':{}},{'session':{}},{'session':{}})]:
            with self.assertRaisesRegex(ValueError, 'INVALID_COMMUNICATION_SOURCE'):
                build_communication_evidence(source)

    def proposal(self, view, *, anchor=2, ids=None):
        return {'schema': PROPOSAL_SCHEMA, 'rubric_version': RUBRIC,
                'evidence_sha256': view['sha256'], 'assessor_kind': 'MODEL_PROPOSAL',
                'question_index': 0, 'dimension_id': 'C01', 'anchor': anchor,
                'cited_candidate_events': ids if ids is not None else ['c-1'],
                'reason': 'Candidate asked about null handling, but appropriateness requires human contextual review.'}

    def test_assessor_proposal_valid_but_not_a_score(self):
        view = build_communication_evidence(data_plan(rec(event('c-1'))))
        result = validate_review_proposal(self.proposal(view), view)
        self.assertEqual(result['status'], 'PENDING_HUMAN_REVIEW')
        self.assertEqual(result['authoritative_communication_score'], 'NOT_SCORED')
        self.assertIsNone(result['proposed_points'])
        self.assertEqual(result['cited_candidate_events'], ['c-1'])

    def test_unauthenticated_forged_proposal_and_invalid_anchors_rejected(self):
        view = build_communication_evidence(data_plan(rec(event('c-1'))))
        for override in ({'anchor': True},{'anchor': 5},{'anchor': -1},
                         {'assessor_kind': 'APPROVED'}, {'question_index': 7},
                         {'cited_candidate_events': ['fake']}, {'cited_candidate_events': ['c-1','c-1']},
                         {'evidence_sha256': '0'*64},{'reason': 'nice'}, {'dimension_id':'C06'}):
            prop = self.proposal(view);prop.update(override)
            with self.assertRaises(ValueError):validate_review_proposal(prop,view)

    def test_tampered_projection_rejects_assessor_proposal(self):
        view = build_communication_evidence(data_plan(rec(event('c-1'))))
        prop = self.proposal(view)
        view['questions'][0]['dimensions'][0]['evidence'][0]['preview']='altered'
        with self.assertRaisesRegex(ValueError,'INVALID_EVIDENCE_SOURCE'):
            validate_review_proposal(prop,view)

    def test_offline_legacy_rehearsal_retains_unknowns(self):
        view = build_communication_evidence(data_plan({'outcome':'DISCUSSION_ONLY'}))
        self.assertEqual(view['questions'][0]['candidate_event_count'],0)
        self.assertEqual(view['questions'][0]['dimensions'][4]['status'],'NOT_OBSERVED')


class CommunicationHostTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp = e3a_tests.ScorecardHostIntegrationTests.asyncSetUp
    asyncTearDown = e3a_tests.ScorecardHostIntegrationTests.asyncTearDown
    cmd = e3a_tests.ScorecardHostIntegrationTests.cmd
    inspected = e3a_tests.ScorecardHostIntegrationTests.inspected
    grade = e3a_tests.ScorecardHostIntegrationTests.grade
    configure_sql = e3a_tests.ScorecardHostIntegrationTests.configure_sql
    start = e3a_tests.ScorecardHostIntegrationTests.start
    model = e3a_tests.ScorecardHostIntegrationTests.model
    setup_three = e3a_tests.ScorecardHostIntegrationTests.setup_three

    async def test_host_snapshot_and_export_are_exactly_same_projection(self):
        await self.inspected()
        await self.grade()
        await self.cmd('rehearsal_submit')
        await self.cmd('rehearsal_skip')
        await self.cmd('rehearsal_skip')
        observed=self.host.state()['communication_evidence']
        exported=(await self.cmd('export'))['export']['communication_evidence']
        self.assertEqual(observed,exported)
        self.assertEqual(observed['summary']['communication_competency'],'NOT_SCORED')
        self.assertEqual(observed['questions'][1]['candidate_event_count'],0)

    async def test_reopen_does_not_call_sql_or_any_model(self):
        await self.inspected()
        await self.cmd('rehearsal_submit')
        previous=self.host.state()['communication_evidence']
        self.host.close()
        with patch('tia_runtime.app_host.grade_fixture',side_effect=AssertionError('SQL ran')):
            self.host=await e3a_tests.TutorialHost.open(self.directory.name)
            self.assertEqual(previous,self.host.state()['communication_evidence'])

    async def test_existing_e3a_card_and_saved_digest_unchanged(self):
        await self.inspected()
        before=self.host._state_digest()
        technical=self.host.state()['evidence_scorecard']
        _=self.host.state()['communication_evidence']
        self.assertEqual(before,self.host._state_digest())
        self.assertEqual(technical,self.host.state()['evidence_scorecard'])

if __name__=='__main__':unittest.main()
