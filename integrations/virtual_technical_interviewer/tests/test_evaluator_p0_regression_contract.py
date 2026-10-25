"""P0 regression contract: protocol rejects vs evidence-linked abstention.

Synthetic, offline, no provider/DB, no interview history mutation.
"""
import copy
import unittest

from tia_runtime import native_evaluator as ev
from tia_runtime.evaluator_p0_guards import eligible_aliases


def event(role, kind, ident, text):
    return {'id': ident, 'actor': role, 'kind': kind,
            'provenance': 'LIVE_MODEL' if role == 'interviewer' else 'USER_SAID',
            'payload': {'operation': 'reply' if role == 'interviewer' else kind, 'text': text}}


def inputs(sequence, *, status='NOT_VERIFIED', tested=None):
    plan = {'results': [{'session': {'events': sequence}}]}
    candidates, replies, _ = ev._evidence(plan, 0)
    accuracy = {'status': status, 'candidate_event_id': tested}
    profile = ev.compile_evaluator_profile()
    criteria = ev._criteria(profile, candidates, replies, accuracy)
    packet = {'candidate_evidence': candidates, 'criteria': criteria,
              'local_execution': {'status': status}}
    return candidates, replies, packet


def proposal(packet, **chosen):
    rows = []
    for item in packet['criteria']:
        anch, alias = chosen.get(item['id'], (None, None))
        rows.append([item['id'], anch, [] if alias is None else [alias],
                     'Synthetic reason with explicit source reference.' if anch is not None
                     else 'No behavior was observed for this criterion.'])
    return {'assessments': rows}


class EvaluatorV4CompatibilityTests(unittest.TestCase):
    def test_unverified_t01_model_claim_is_rejected(self):
        _, _, packet = inputs([event('candidate', 'implement', 's1', 'SELECT * FROM Queue')])
        with self.assertRaisesRegex(ev.NativeEvaluatorError, 'EVALUATOR_UNCITED'):
            ev._assessed_dimensions(proposal(packet, T01=(0, 'e1')), packet)

    def test_unverified_stale_t01_model_claim_is_rejected(self):
        seq = [event('candidate', 'implement', 's1', 'SELECT * FROM Queue'),
               event('candidate', 'implement', 's2', 'SELECT 99')]
        _, _, packet = inputs(seq, status='NOT_VERIFIED', tested='s1')
        with self.assertRaisesRegex(ev.NativeEvaluatorError, 'EVALUATOR_UNCITED'):
            ev._assessed_dimensions(proposal(packet, T01=(0, 'e1')), packet)

    def test_failed_sql_may_receive_evidenced_anchor_zero_not_positive(self):
        _, _, packet = inputs([event('candidate', 'implement', 's1', 'SELECT 1')], status='FAILED', tested='s1')
        value = ev._assessed_dimensions(proposal(packet, T01=(0, 'e1')), packet)[0]
        self.assertEqual(value['anchor_0_to_4'], 0)
        self.assertEqual(value['provisional_points'], 0)
        with self.assertRaisesRegex(ev.NativeEvaluatorError, 'FAILED_SQL_CANNOT_PASS'):
            ev._assessed_dimensions(proposal(packet, T01=(2, 'e1')), packet)

    def test_unsupported_c06_model_claim_is_rejected(self):
        _, _, packet = inputs([event('candidate', 'plan', 's1', 'I will discuss my plan.')])
        with self.assertRaisesRegex(ev.NativeEvaluatorError, 'EVALUATOR_UNCITED'):
            ev._assessed_dimensions(proposal(packet, C06=(2, 'e1')), packet)

    def test_code_only_c01_and_t04_are_audited_not_awarded(self):
        _, _, packet = inputs([event('interviewer', 'reply', 'i1', 'Tell me your approach.'),
                               event('candidate', 'implement', 's1', 'SELECT * FROM Queue')])
        result = ev._assessed_dimensions(proposal(packet, T04=(2, 'e1'), C01=(2, 'e1')), packet)
        for dim in (result[3], result[5]):
            self.assertIsNone(dim['anchor_0_to_4'])
            self.assertIsNone(dim['provisional_points'])
            self.assertEqual(dim['admissibility_audit']['gate'], 'CRITERION_EVIDENCE_INADMISSIBLE')

    def test_specific_followup_feedback_can_be_considered(self):
        sequence = [event('candidate','clarify','c1','What are the expected output constraints?'),
                    event('candidate','implement','s1','SELECT person_name FROM Queue'),
                    event('interviewer','reply','i1','Explain the join cardinality before choosing an index.'),
                    event('candidate','plan','c2','I will explain each join and then check cardinality.')]
        c, replies, packet = inputs(sequence)
        self.assertEqual(eligible_aliases('C05', c, replies, {'status':'NOT_VERIFIED'}), ['e3'])
        dim = ev._assessed_dimensions(proposal(packet, C05=(2, 'e3')), packet)[9]
        self.assertEqual(dim['anchor_0_to_4'], 2)
        self.assertEqual(dim['confidence'], 'HUMAN_REVIEW_REQUIRED')

    def test_initial_interviewer_request_not_feedback(self):
        c, replies, _ = inputs([event('interviewer','reply','i1','Explain the plan.'),
                                event('candidate','implement','s1','SELECT * FROM Queue')])
        self.assertEqual(eligible_aliases('C05', c, replies, {'status':'NOT_VERIFIED'}), [])

    def test_v3_source_hashes_exact_whitelist(self):
        self.assertEqual(ev.P0_V3_CODE_SOURCES['engine/native_evaluator.py'],
                         'b6c73382e9a0463a692119aac00727df32d80ec4ef0714a2c137210e24729e49')
        self.assertEqual(ev.P0_V3_CODE_SOURCES['engine/evaluator_p0_guards.py'],
                         '5a4760465f0b617a1a658cfe990752227e62d97da90b3720fc4668b2d349dc64')
        self.assertNotEqual(ev._p0_code_sources(), ev.P0_V3_CODE_SOURCES)

    def test_unchanged_synthetic_proposal_does_not_mutate_input(self):
        _, _, packet = inputs([event('candidate','implement','s1','SELECT 1')])
        p = proposal(packet, C01=(3,'e1'))
        original = copy.deepcopy(p)
        ev._assessed_dimensions(p, packet)
        self.assertEqual(p, original)

if __name__ == '__main__':
    unittest.main()
