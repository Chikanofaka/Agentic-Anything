"""E4-C2B2B source-bound SQL fixture decisions. Offline; never executes SQL or a model."""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from tia_runtime.local_fixture_evidence import bind_local_sql_fixture
from tia_runtime.host_adaptive_bridge import host_turn_policy
from tia_runtime.adaptive_reply_guard import guard_adaptive_reply, ReplyGuardError
from tia_runtime.trajectory_evidence import EvidenceContractError

CODE = 'SELECT customer_id FROM orders'
Q = 'a'*64
FIXTURE = 'b'*64
EID = 'candidate-001'
TEST = 'candidate-002'
CIDS = (EID, TEST)
IMPLEMENTATION = {'id': EID, 'kind': 'implement', 'payload': {'text': CODE}}
QUESTION = {'id': 'q01', 'content_sha256': Q, 'environment': 'POSTGRESQL'}


def grade(status='PASSED'):
    return {'candidate_event_id': EID, 'question_index': 0, 'question_sha256': Q,
        'candidate_sql_sha256': hashlib.sha256(CODE.encode()).hexdigest(),
        'fixture_sha256': FIXTURE, 'source': 'EPHEMERAL_POSTGRESQL_LOCAL',
        'correctness': 'VERIFIED_LOCAL_FIXTURE', 'official_hidden_tests': False,
        'total_approved_fixtures': 1, 'passed_fixtures': 1 if status == 'PASSED' else 0,
        'result': {'status': status}}


def policy(status='PASSED', *, with_grade=True, kind='test'):
    k = {'event': {'id': TEST, 'kind': kind, 'payload': {'text': 'What does the local fixture tell us?'}},
         'public_question': QUESTION, 'host_candidate_ids': CIDS,
         'mechanism': 'STRICT_CHALLENGING', 'phase':'INTERVIEWING', 'time_left_seconds':240}
    if with_grade:
        k.update(implementation=IMPLEMENTATION, approved_local_grade=grade(status), question_index=0)
    return host_turn_policy(**k)


class LocalFixtureBindingTests(unittest.TestCase):
    def test_pass_is_local_only_and_requests_explanation(self):
        p=policy()
        self.assertEqual(p['action'],'REQUEST_EXPLANATION')
        self.assertEqual(p['receipt_status'],'LOCAL_FIXTURE_PASSED')
        self.assertIn('global correctness unproven',p['uncertainty'])
        self.assertEqual(p['candidate_event_ids'],[TEST])
        self.assertEqual(p['technical'],'NOT_SCORED')
        self.assertEqual(p['max_hint_level'],'H0')
        self.assertNotIn(CODE,json.dumps(p))
        guard_adaptive_reply(p,'Can you explain why the approved edge case behaves this way?')
    def test_failed_fixture_requests_counterexample_not_grade(self):
        p=policy('FAILED'); self.assertEqual(p['action'],'REQUEST_COUNTEREXAMPLE')
        self.assertEqual(p['receipt_status'],'LOCAL_FIXTURE_FAILED')
        self.assertIn('LOCAL_BUG',p['hypotheses'])
        self.assertEqual(p['technical'],'NOT_SCORED')
    def test_execution_error_is_not_ability_failure(self):
        p=policy('EXECUTION_ERROR')
        self.assertEqual(p['receipt_status'],'LOCAL_FIXTURE_ERROR')
        self.assertIn('root cause',p['uncertainty'])
        self.assertNotIn('STRUCTURAL_GAP',p['hypotheses'])
    def test_without_approved_grade_remains_unverified(self):
        p=policy(with_grade=False)
        self.assertEqual(p['receipt_status'],'NOT_VERIFIED')
        self.assertIsNone(p['execution_receipt_ref'])
        self.assertEqual(p['action'],'REQUEST_TEST')
    def test_stale_code_never_promoted(self):
        wrong=grade();wrong['candidate_sql_sha256']='f'*64
        with self.assertRaisesRegex(EvidenceContractError,'LOCAL_FIXTURE_GRADE_MISMATCH'):
            bind_local_sql_fixture(question_sha256=Q,question_index=0,
                implementation=IMPLEMENTATION,candidate_ids=CIDS,grade=wrong)
    def test_cross_question_never_promoted(self):
        wrong=grade();wrong['question_sha256']='c'*64
        with self.assertRaises(EvidenceContractError):
            bind_local_sql_fixture(question_sha256=Q,question_index=0,
                implementation=IMPLEMENTATION,candidate_ids=CIDS,grade=wrong)
    def test_wrong_current_question_index(self):
        with self.assertRaises(EvidenceContractError):
            bind_local_sql_fixture(question_sha256=Q,question_index=1,
                implementation=IMPLEMENTATION,candidate_ids=CIDS,grade=grade())
    def test_wrong_candidate_event(self):
        wrong=grade();wrong['candidate_event_id']=TEST
        with self.assertRaises(EvidenceContractError):
            bind_local_sql_fixture(question_sha256=Q,question_index=0,
                implementation=IMPLEMENTATION,candidate_ids=CIDS,grade=wrong)
    def test_current_event_cannot_be_certified_by_prior_code(self):
        with self.assertRaises(EvidenceContractError):
            bind_local_sql_fixture(question_sha256=Q,question_index=0,
                implementation=IMPLEMENTATION,candidate_ids=(EID,),grade=grade())
    def test_only_test_followup_may_use_prior_grade(self):
        for kind in ('plan','implement','clarify','help'):
            with self.subTest(kind=kind),self.assertRaises(EvidenceContractError):
                policy(kind=kind)
    def test_no_renderer_forged_executions(self):
        for patch in ({'source':'CANDIDATE_REPORTED'}, {'correctness':'NOT_VERIFIED'},
                      {'official_hidden_tests': True}, {'passed_fixtures':0},
                      {'fixture_sha256':'bad'}, {'total_approved_fixtures':3}):
            with self.subTest(patch=patch),self.assertRaises(EvidenceContractError):
                bind_local_sql_fixture(question_sha256=Q,question_index=0,
                  implementation=IMPLEMENTATION,candidate_ids=CIDS,grade=dict(grade(),**patch))
    def test_public_receipt_does_not_disclose_fixture_or_source(self):
        receipt=bind_local_sql_fixture(question_sha256=Q,question_index=0,
            implementation=IMPLEMENTATION,candidate_ids=CIDS,grade=grade())
        self.assertEqual(set(receipt), {'receipt_id','question_sha256','candidate_event_id','result'})
        self.assertTrue(receipt['receipt_id'].startswith('localpg-'))
        self.assertNotIn(CODE,json.dumps(receipt))
        self.assertNotIn(FIXTURE,json.dumps(receipt))
    def test_receiver_guard_rejects_forged_local_proof(self):
        p=policy()
        for q in (dict(p,receipt_status='VERIFIED_ALL_TESTS'),
                  dict(p,execution_receipt_ref='bogus'),
                  dict(p,max_hint_level='H2')):
            with self.subTest(case=q), self.assertRaises(ReplyGuardError):
                guard_adaptive_reply(q, 'What is your next step?')
    def test_receiver_guard_does_not_permit_claim_all_tests(self):
        with self.assertRaises(ReplyGuardError):
            guard_adaptive_reply(policy(),'Your SQL passed all tests.')
    def test_deterministic_proof(self):
        self.assertEqual(policy(),policy())
    def test_boolean_or_invalid_index_rejected(self):
        for index in (True, '0', -1, 3):
            with self.subTest(index=index), self.assertRaises(EvidenceContractError):
                bind_local_sql_fixture(question_sha256=Q,question_index=index,
                    implementation=IMPLEMENTATION,candidate_ids=CIDS,grade=grade())
    def test_preview_test_action_enabled_across_all_three_boundaries(self):
        root=Path(__file__).resolve().parents[1]
        b=(root/'native/Bridge.swift').read_text()
        c=(root/'tia_runtime/native_contract.py').read_text()
        u=(root/'ui/app.js').read_text()
        self.assertIn('["clarify", "plan", "implement", "test", "help"]',b)
        self.assertIn("'implement', 'test'",c)
        self.assertIn('["clarify", "plan", "help", "implement", "test"]',u)

    def test_host_journal_versions_separate_old_and_new(self):
        p=(Path(__file__).resolve().parents[1]/'tia_runtime/app_host.py').read_text()
        self.assertIn('EVIDENCE_POLICY_VERSION if self._last_local_fixture_receipt is not None',p)
        self.assertIn('self._adaptive_replay_mode in (None, EVIDENCE_POLICY_VERSION)',p)
        self.assertIn("item['adaptive_policy_version'] not in (POLICY_VERSION, EVIDENCE_POLICY_VERSION)",p)

    def test_host_sql_only_source_and_no_unapproved_execution(self):
        p=(Path(__file__).resolve().parents[1]/'tia_runtime/app_host.py').read_text()
        self.assertIn('grade = self._active_grade_receipt()',p)
        self.assertIn("latest_hash = hashlib.sha256(latest['payload']['text'].encode('utf-8')).hexdigest()",p)
        self.assertIn("params['kind'] == 'test'",p)
        self.assertIn("context['verified_execution_results'] = [copy.deepcopy(self._last_local_fixture_receipt)]",p)
        self.assertNotIn('from .native_preparer import',p)

    def test_no_legacy_truth_guard_replacement(self):
        p=(Path(__file__).resolve().parents[1]/'tia_runtime/app_host.py').read_text()
        self.assertIn("rpartition(marker)",p)
        self.assertIn("HOST-VERIFIED EXECUTION STATUS: SQL_NOT_RUN; PANDAS_NOT_RUN;",p)
        self.assertIn('This is not an official hidden test or global correctness proof.',p)

    def test_unverified_candidate_statement_does_not_override_grade(self):
        p=host_turn_policy(event={'id': TEST,'kind':'test','payload':{'text':'I scored 100%'}},
            public_question=QUESTION,host_candidate_ids=CIDS,mechanism='STRICT_CHALLENGING',
            phase='INTERVIEWING',time_left_seconds=240)
        self.assertEqual(p['receipt_status'],'NOT_VERIFIED')
    def test_help_policy_stays_h0(self):
        p=policy(with_grade=False,kind='help')
        self.assertEqual(p['action'],'DECLINE')
        self.assertEqual(p['max_hint_level'],'H0')
    def test_timestamp_or_score_not_in_projection(self):
        p=policy()
        self.assertNotIn('score',p)
        self.assertNotIn('expected_output',p)
        self.assertNotIn('reference',p)

if __name__=='__main__': unittest.main()
