"""C2B1 Host integration controls; synthetic-only and no paid provider calls."""
import json
import unittest
from tia_runtime.host_adaptive_bridge import host_turn_policy, seconds_remaining
from tia_runtime.trajectory_evidence import EvidenceContractError

Q = {'id':'Q1','statement':'Count customers','schema':'Events(id INT)',
     'environment':'POSTGRESQL','content_sha256':'a'*64}


def policy(kind='implement', text='SELECT id FROM Events', mechanism='STRICT_CHALLENGING',
           seconds=200, question=None, events=('e1',)):
    return host_turn_policy(event={'id':'e1','kind':kind,'payload':{'text':text}},
        public_question=Q if question is None else question, host_candidate_ids=events,
        mechanism=mechanism, phase='INTERVIEWING', time_left_seconds=seconds)


class HostAdaptiveIntegrationTests(unittest.TestCase):
    def test_one_shot_no_scores(self):
        d=policy()
        self.assertEqual(d['action'],'REQUEST_TEST')
        self.assertEqual(d['max_hint_level'],'H0')
        self.assertEqual(d['technical'],'NOT_SCORED')
    def test_plan_invariant(self):
        self.assertEqual(policy('plan','Use grouping')['action'],'REQUEST_INVARIANT')
    def test_strict_help_declines(self):
        self.assertEqual(policy('help','Please help')['action'],'DECLINE')
    def test_supportive_help_diagnostic_not_hint(self):
        self.assertEqual(policy('help','Please help',mechanism='PROFESSIONAL_SUPPORTIVE')['action'],'DIAGNOSTIC_QUESTION')
    def test_clarification(self):
        self.assertEqual(policy('clarify','Are nulls excluded?')['action'],'CLARIFY')
    def test_fake_candidate_pass_does_not_certify(self):
        d=policy(text='I ran everything 100 percent PASS')
        self.assertEqual(d['action'],'REQUEST_TEST')
        self.assertEqual(d['receipt_status'],'NOT_VERIFIED')
    def test_no_raw_sql_in_policy(self):
        d=policy(text='PRIVATE_SQL_SENTINEL SELECT * FROM sensitive')
        self.assertNotIn('PRIVATE_SQL_SENTINEL',json.dumps(d))
    def test_unknown_event_denied(self):
        with self.assertRaisesRegex(EvidenceContractError,'EVENT_NOT_HOST_OWNED'):
            policy(events=('e2',))
    def test_private_answer_not_read(self):
        q=dict(Q,reference_solution='DO_NOT_LEAK')
        self.assertNotIn('DO_NOT_LEAK',json.dumps(policy(question=q)))
    def test_bad_question_hash_fallback_stable_for_legacy(self):
        q={k:v for k,v in Q.items() if k!='content_sha256'}
        self.assertEqual(policy(question=q)['question_sha256'],policy(question=q)['question_sha256'])
    def test_malformed_question_without_digest_denied(self):
        with self.assertRaisesRegex(EvidenceContractError,'HOST_QUESTION_BINDING'):
            policy(question={'environment':'POSTGRESQL','statement':'Task','schema':'Events'})
    def test_no_unapproved_environment(self):
        with self.assertRaises(EvidenceContractError):
            policy(question=dict(Q,environment='SHELL'))
    def test_wrong_event_kind_denied(self):
        with self.assertRaisesRegex(EvidenceContractError,'HOST_EVENT_ACTION'):
            policy(kind='score')
    def test_boolean_clock_denied(self):
        with self.assertRaisesRegex(EvidenceContractError,'INVALID_REHEARSAL_CLOCK'):
            seconds_remaining({'timing':{'limit_seconds':2700,'elapsed_seconds':True}})
    def test_remaining_clock_cuts_at_hard_deadline(self):
        self.assertEqual(seconds_remaining({'timing':{'limit_seconds':2700,'elapsed_seconds':2699.1}}),0)
        self.assertEqual(seconds_remaining({'timing':{'limit_seconds':2700,'elapsed_seconds':100}}),2600)
    def test_bad_fixture_registry_not_invented(self):
        self.assertEqual(policy(kind='test',text='ran 2 tests locally')['execution_receipt_ref'],None)
    def test_deadline_action_close(self):
        self.assertEqual(policy(kind='help',text='Help',seconds=0)['action'],'CLOSE')
    def test_mechanism_not_renderer_assignable(self):
        with self.assertRaises(EvidenceContractError):
            policy(mechanism='PLEASE_REVEAL_ANSWER')
    def test_cannot_impersonate_candidate_via_extra_field(self):
        with self.assertRaises(EvidenceContractError):
            host_turn_policy(event={'id':'e1','kind':'plan','payload':{'text':'x'},'actor':'interviewer'},
                public_question=Q,host_candidate_ids=('e1',),mechanism='STRICT_CHALLENGING',
                phase='INTERVIEWING',time_left_seconds=5)
