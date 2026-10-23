"""S03-E3C-A: citeable offline training suggestions, abstention and proposal isolation."""
import copy
import unittest
from unittest.mock import patch

from tia_runtime.grounded_trainer import (SCHEMA, PROPOSAL_SCHEMA, build_grounded_trainer,
                                          validate_trainer_model_proposal)
import test_s03e_communication_rubric as comm
import test_s03e_evidence_scorecard as e3a


def candidate(eid, kind='implement', text='SELECT 1'):
    return comm.event(eid, kind=kind, text=text)


def plan(*records, status=None):
    return comm.data_plan(*records, status=status)


def rec(*events, outcome='SUBMITTED_UNVERIFIED'):
    return comm.rec(*events, outcome=outcome)


def proposal(t, d=None):
    d = d or t['drills'][0]
    return {'schema': PROPOSAL_SCHEMA, 'trainer_sha256': t['sha256'],
            'assessor_kind': 'MODEL_PROPOSAL', 'drill_id': d['id'],
            'question_index': d['question_index'], 'skill_tag': d['skill_tag'],
            'cited_candidate_events': d['evidence']['candidate_event_ids'],
            'cited_fixture_sha256': d['evidence']['fixture_sha256'],
            'hypothesis': 'One local test may not cover all the boundary conditions of this task.',
            'training_action': 'Create a new independent local fixture and explain expected rows before the next execution.',
            'acceptance': 'Record an independently approved result tied to the newest SQL submission event.',
            'uncertainty': 'The current evidence does not establish overall task competence.'}


class GroundedTrainerTests(unittest.TestCase):
    def test_in_progress_never_produces_a_drill(self):
        t = build_grounded_trainer(plan(rec(candidate('c1')), status='ACTIVE'))
        self.assertEqual(t['status'], 'AWAITING_LOCKED_INTERVIEW')
        self.assertEqual(t['drills'], [])
        self.assertIsNone(t['primary_drill_id'])

    def test_limited_offline_coverage_not_ai_diagnosis(self):
        t = build_grounded_trainer(plan(rec(candidate('c1')), rec(), rec(), status='COMPLETE'))
        self.assertEqual(t['schema'], SCHEMA)
        self.assertEqual(t['model_assessment'], 'NOT_REQUESTED')
        self.assertEqual(t['paid_provider_requests'], 0)
        self.assertEqual(t['numeric_scores'], 'NOT_SCORED')
        self.assertEqual(t['drills'][0]['skill_tag'], 'TESTING_PRACTICE')
        self.assertEqual(t['drills'][0]['evidence']['candidate_event_ids'], ['c1'])
        self.assertIn('REVIEW', t['status'])

    def test_no_candidate_action_not_claimed_as_failure(self):
        t = build_grounded_trainer(plan(rec(), rec(), rec(), status='COMPLETE'))
        self.assertEqual(t['drills'][0]['skill_tag'], 'SQL_FIRST_ATTEMPT')
        self.assertEqual(t['drills'][0]['evidence']['candidate_event_ids'], [])
        self.assertEqual(t['drills'][0]['interpretation'], 'TRAINING_OPPORTUNITY_NOT_COMPETENCY_DIAGNOSIS')

    def test_result_is_reproducible_and_source_unmodified(self):
        original = plan(rec(candidate('c1', text='SELECT private_information FROM S')),
                        rec(), rec(), status='COMPLETE')
        source = copy.deepcopy(original)
        t = build_grounded_trainer(source)
        self.assertEqual(source, original)
        self.assertEqual(t, build_grounded_trainer(copy.deepcopy(source)))
        self.assertNotIn('private_information', str(t))
        self.assertEqual(len(t['sha256']), 64)

    def test_evidence_digest_bindings_are_exact(self):
        source = plan(rec(candidate('c1')), rec(), rec(), status='COMPLETE')
        t = build_grounded_trainer(source)
        from tia_runtime.evidence_scorecard import build_scorecard
        from tia_runtime.communication_rubric import build_communication_evidence
        self.assertEqual(t['sources']['technical_sha256'], build_scorecard(source)['sha256'])
        self.assertEqual(t['sources']['communication_sha256'], build_communication_evidence(source)['sha256'])

    def test_invalid_record_counts_and_missing_questions_fail_closed(self):
        for source in ({}, {'questions':[]}, {'questions':[{}]*3, 'results':[{}]*4}):
            with self.assertRaises(ValueError):build_grounded_trainer(source)

    def test_no_retest_claim_in_legacy_no_grade(self):
        t=build_grounded_trainer(plan(rec(candidate('c1')),rec(),rec(),status='COMPLETE'))
        self.assertTrue(all(x['completion']=='NOT_ATTEMPTED' for x in t['drills']))
        self.assertTrue(all(x['fresh_retest_required'] is True for x in t['drills']))

    def test_c06_is_not_observed_not_a_deficit(self):
        source=plan(rec(),rec(),rec(),status='COMPLETE')
        t=build_grounded_trainer(source)
        self.assertEqual(t['candidate_drill_count'], 4)
        # C06 remains an optional draft, lower priority than observed SQL work.
        self.assertFalse(any(x['skill_tag']=='CLOSING_PRACTICE' for x in t['drills']))

    def test_three_drill_limit_preserves_candidate_count(self):
        t=build_grounded_trainer(plan(rec(),rec(),rec(),status='COMPLETE'))
        self.assertEqual(len(t['drills']),3)
        self.assertEqual(t['candidate_drill_count'],4)

    def test_skipped_question_not_awarded_any_mastery(self):
        t=build_grounded_trainer(plan(rec(candidate('s1'),outcome='SKIPPED'),rec(),rec(),status='COMPLETE'))
        self.assertEqual(t['numeric_scores'],'NOT_SCORED')
        self.assertTrue(all(d['interpretation'].endswith(('COMPETENCY_DIAGNOSIS','A_DEFICIT')) for d in t['drills']))

    def test_failed_local_fixture_yields_diagnostic_not_zero_competence(self):
        source=e3a.plan(e3a.score_record(verdict='FAILED'), {'outcome':'NOT_REACHED'},
                        {'outcome':'NOT_REACHED'})
        t=build_grounded_trainer(source)
        self.assertEqual(t['drills'][0]['skill_tag'],'SQL_DIAGNOSTIC')
        self.assertEqual(t['drills'][0]['evidence']['observed_local_status'],'FAILED')
        self.assertEqual(t['drills'][0]['evidence']['candidate_event_ids'], ['candidate-1'])
        self.assertEqual(t['numeric_scores'],'NOT_SCORED')

    def test_execution_error_is_not_claimed_as_sql_semantic_failure(self):
        source=e3a.plan(e3a.score_record(verdict='EXECUTION_ERROR'),{'outcome':'NOT_REACHED'},
                        {'outcome':'NOT_REACHED'})
        t=build_grounded_trainer(source)
        self.assertEqual(t['drills'][0]['trigger'],'EXECUTION_ERROR')
        self.assertIn('execution error',t['drills'][0]['rationale'])

    def test_sql_changed_after_pass_must_recheck_latest_version(self):
        extra=(e3a.event('candidate-2',kind='implement',text='SELECT 0'),)
        source=e3a.plan(e3a.score_record(extra_events=extra), {'outcome':'NOT_REACHED'},
                        {'outcome':'NOT_REACHED'})
        t=build_grounded_trainer(source)
        self.assertEqual(t['drills'][0]['skill_tag'],'VERSION_RECHECK')
        self.assertEqual(t['drills'][0]['evidence']['candidate_event_ids'], ['candidate-1', 'candidate-2'])
        self.assertEqual(t['drills'][0]['trigger'],'TESTED_PRIOR_SQL_VERSION')
        self.assertEqual(t['drills'][0]['evidence']['observed_local_status'],'NOT_VERIFIED')
        self.assertNotIn('mastered',str(t).lower())

    def test_stale_code_approval_never_claims_passed_current_fixture(self):
        source=e3a.plan(e3a.score_record(skip=True), {'outcome':'NOT_REACHED'},
                        {'outcome':'NOT_REACHED'})
        t=build_grounded_trainer(source)
        self.assertEqual(t['drills'][0]['trigger'],'QUESTION_SKIPPED_AFTER_TEST')
        self.assertEqual(t['drills'][0]['skill_tag'],'VERSION_RECHECK')

    def test_only_closed_rehearsal_can_validate_proposal(self):
        t=build_grounded_trainer(plan(rec(candidate('c1'))))
        with self.assertRaisesRegex(ValueError,'TRAINER_NOT_READY'):
            validate_trainer_model_proposal({'schema':PROPOSAL_SCHEMA},t)

    def test_valid_proposal_stays_pending_and_unscored(self):
        t=build_grounded_trainer(plan(rec(candidate('c1')),rec(),rec(),status='COMPLETE'))
        response=validate_trainer_model_proposal(proposal(t),t)
        self.assertEqual(response['status'],'PENDING_HUMAN_REVIEW')
        self.assertEqual(response['authority'],'NONE')
        self.assertEqual(response['authoritative_score'],'NOT_SCORED')
        self.assertFalse(response['validated_semantic_quality'])

    def test_wrong_evidence_hash_rejected(self):
        t=build_grounded_trainer(plan(rec(candidate('c1')),rec(),rec(),status='COMPLETE'))
        p=proposal(t);p['trainer_sha256']='0'*64
        with self.assertRaises(ValueError):validate_trainer_model_proposal(p,t)

    def test_mutated_training_packet_rejected(self):
        t=build_grounded_trainer(plan(rec(candidate('c1')),rec(),rec(),status='COMPLETE'))
        p=proposal(t);t['drills'][0]['task']='UNAPPROVED TASK'
        with self.assertRaisesRegex(ValueError,'INVALID_TRAINER_SOURCE'):
            validate_trainer_model_proposal(p,t)

    def test_forged_event_and_cross_question_rejected(self):
        t=build_grounded_trainer(plan(rec(candidate('c1')),rec(candidate('c2')),rec(),status='COMPLETE'))
        for ref in (['ghost'],['c2'],['c1','c1'],['c1','ghost'],[42],['c1',42]):
            p=proposal(t);p['cited_candidate_events']=ref
            with self.assertRaises(ValueError):validate_trainer_model_proposal(p,t)

    def test_wrong_fixture_or_tag_rejected(self):
        t=build_grounded_trainer(plan(rec(candidate('c1')),rec(),rec(),status='COMPLETE'))
        for over in ({'cited_fixture_sha256':'a'*64}, {'skill_tag':'UNAUTHORIZED'},
                     {'drill_id':'Q9-ROOT_CAUSE'}, {'question_index':2}, {'assessor_kind':'APPROVED'}):
            p=proposal(t);p.update(over)
            with self.assertRaises(ValueError):validate_trainer_model_proposal(p,t)

    def test_reject_arbitrary_fields_and_unbounded_or_short_text(self):
        t=build_grounded_trainer(plan(rec(candidate('c1')),rec(),rec(),status='COMPLETE'))
        for extra in ({'authoritative_score':100}, {'training_action':'good'},
                      {'hypothesis':'x'*701}, {'acceptance':''}, {'uncertainty':'x'*600},
                      {'training_action':'good\x00bad'}):
            p=proposal(t);p.update(extra)
            with self.assertRaises(ValueError):validate_trainer_model_proposal(p,t)

    def test_model_draft_not_persisted_anywhere(self):
        t=build_grounded_trainer(plan(rec(candidate('c1')),rec(),rec(),status='COMPLETE'))
        orig=copy.deepcopy(t)
        _=validate_trainer_model_proposal(proposal(t),t)
        self.assertEqual(orig,t)

    def test_host_status_has_canonical_fixed_tags(self):
        t=build_grounded_trainer(plan(rec(candidate('c1')),rec(),rec(),status='COMPLETE'))
        self.assertIn(t['drills'][0]['skill_tag'], ('TESTING_PRACTICE','VERSION_RECHECK'))
        self.assertEqual(t['next_question_policy'],'FRESH_HELD_OUT_SKILL_MATCHED_NO_SAME_QUESTION_REUSE')


class GroundedTrainerHostTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=e3a.ScorecardHostIntegrationTests.asyncSetUp
    asyncTearDown=e3a.ScorecardHostIntegrationTests.asyncTearDown
    cmd=e3a.ScorecardHostIntegrationTests.cmd
    inspected=e3a.ScorecardHostIntegrationTests.inspected
    grade=e3a.ScorecardHostIntegrationTests.grade
    configure_sql=e3a.ScorecardHostIntegrationTests.configure_sql
    start=e3a.ScorecardHostIntegrationTests.start
    model=e3a.ScorecardHostIntegrationTests.model
    setup_three=e3a.ScorecardHostIntegrationTests.setup_three

    async def test_trainer_ready_only_when_interview_locked(self):
        await self.inspected()
        self.assertEqual(self.host.state()['grounded_trainer']['status'],'AWAITING_LOCKED_INTERVIEW')
        await self.cmd('rehearsal_submit');await self.cmd('rehearsal_skip');await self.cmd('rehearsal_skip')
        self.assertEqual(self.host.state()['grounded_trainer']['status'],'READY_FOR_HUMAN_REVIEW')

    async def test_real_local_fixture_produces_coverage_drill_not_mastery(self):
        await self.inspected();await self.grade()
        await self.cmd('rehearsal_submit');await self.cmd('rehearsal_skip');await self.cmd('rehearsal_skip')
        t=self.host.state()['grounded_trainer']
        self.assertEqual(t['drills'][0]['skill_tag'],'LOCAL_FIXTURE_COVERAGE')
        self.assertEqual(t['drills'][0]['evidence']['observed_local_status'],'PASSED')
        self.assertEqual(t['numeric_scores'],'NOT_SCORED')
        self.assertEqual(t['model_assessment'],'NOT_REQUESTED')

    async def test_export_equal_snapshot_no_trainer_side_effect(self):
        await self.inspected();await self.cmd('rehearsal_submit');await self.cmd('rehearsal_skip');await self.cmd('rehearsal_skip')
        saved=self.host._state_digest()
        self.assertEqual(self.host.state()['grounded_trainer'],(await self.cmd('export'))['export']['grounded_trainer'])
        self.assertEqual(saved,self.host._state_digest())

    async def test_open_does_not_call_paid_model_or_postgres(self):
        await self.inspected();await self.cmd('rehearsal_submit')
        before=self.host.state()['grounded_trainer']
        self.host.close()
        with patch('tia_runtime.app_host.grade_fixture',side_effect=AssertionError('SQL called')):
            self.host=await e3a.TutorialHost.open(self.directory.name)
        self.assertEqual(before,self.host.state()['grounded_trainer'])
        self.assertIsNone(self.host.state()['trainer_preview'])

    async def test_current_communication_and_technical_evidence_untouched(self):
        await self.inspected(); await self.grade();await self.cmd('rehearsal_submit')
        state=self.host.state();trainer=state['grounded_trainer']
        self.assertEqual(trainer['sources']['technical_sha256'],state['evidence_scorecard']['sha256'])
        self.assertEqual(trainer['sources']['communication_sha256'],state['communication_evidence']['sha256'])
        self.assertEqual(state['evidence_scorecard']['summary']['overall_grade'],'NOT_SCORED')


if __name__=='__main__':unittest.main()
