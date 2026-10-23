"""E4-C2A contract-only deterministic Host decisions; no model or SQL calls."""
import json
import unittest

from tia_runtime.trajectory_evidence import project_observation, EvidenceContractError
from tia_runtime.interviewer_decision import decide_turn, validate_model_reply, public_interviewer_packet

SHA = 'a' * 64
OTHER_SHA = 'b' * 64


def make_obs(kind='IMPLEMENT', body='SELECT customer_id FROM t', receipt=None,
             registry=(), question_sha=SHA, known=('candidate-01',), eid='candidate-01', environment='POSTGRESQL'):
    return project_observation(event={'event_id': eid, 'kind': kind, 'text': body},
                               known_event_ids=known, question_sha256=question_sha,
                               question_environment=environment, receipt_ref=receipt,
                               host_receipts=registry)


def make_receipt(result='PASSED', question_sha=SHA, eid='candidate-01'):
    return {'receipt_id': 'local-fixture-01', 'question_sha256': question_sha,
            'candidate_event_id': eid, 'result': result}


def make_decision(kind='IMPLEMENT', *, mechanism='STRICT_CHALLENGING',
                  phase='INTERVIEWING', seconds=600, receipt=None, registry=()):
    return decide_turn(observation=make_obs(kind=kind, receipt=receipt, registry=registry),
                       phase=phase, time_left_seconds=seconds, mechanism=mechanism,
                       host_receipts=registry)


class C2AAdaptiveDecisionTests(unittest.TestCase):
    def test_canonical_plan_stays_unverified(self):
        d = make_decision('PLAN')
        self.assertEqual(d['authorized_action'], 'REQUEST_INVARIANT')
        self.assertEqual(d['hypotheses'], ['PROMISING_UNVERIFIED', 'UNKNOWN'])

    def test_alternative_unverified_not_rejected(self):
        d = make_decision('PLAN')
        self.assertNotIn('WRONG', json.dumps(d))
        self.assertEqual(d['disclosure_scope'], 'PUBLIC_TASK_ONLY')

    def test_one_shot_sql_without_narration_requests_test(self):
        d = make_decision('IMPLEMENT')
        self.assertEqual(d['authorized_action'], 'REQUEST_TEST')

    def test_no_execution_proof_from_candidate_claim(self):
        d = decide_turn(observation=make_obs(body='I ran the SQL and PASSED 100%'),
                        phase='INTERVIEWING', time_left_seconds=500,
                        mechanism='STRICT_CHALLENGING')
        self.assertEqual(d['authorized_action'], 'REQUEST_TEST')
        self.assertIsNone(d['execution_receipt_ref'])

    def test_real_fixture_pass_only_gives_qualitative_hypotheses(self):
        d = make_decision(receipt='local-fixture-01', registry=(make_receipt(),))
        self.assertEqual(d['authorized_action'], 'REQUEST_EXPLANATION')
        self.assertIn('VALID_ALTERNATIVE', d['hypotheses'])
        self.assertIn('global correctness unproven', d['uncertainty'])
        self.assertNotIn('score', d)

    def test_failed_fixture_requests_counterexample_not_certified_wrong(self):
        d = make_decision(receipt='local-fixture-01', registry=(make_receipt('FAILED'),))
        self.assertEqual(d['authorized_action'], 'REQUEST_COUNTEREXAMPLE')
        self.assertIn('LOCAL_BUG', d['hypotheses'])

    def test_sql_execution_error_not_automatically_a_skill_grade(self):
        d = make_decision(receipt='local-fixture-01', registry=(make_receipt('ERROR'),))
        self.assertIn('root cause', d['uncertainty'])
        self.assertNotIn('STRUCTURAL_GAP', d['hypotheses'])

    def test_strict_help_declined(self):
        d = make_decision('HELP')
        self.assertEqual(d['authorized_action'], 'DECLINE')
        self.assertEqual(d['max_hint_level'], 'H0')

    def test_supportive_help_diagnostic_no_hint_ladder(self):
        d = make_decision('HELP', mechanism='PROFESSIONAL_SUPPORTIVE')
        self.assertEqual(d['authorized_action'], 'DIAGNOSTIC_QUESTION')
        self.assertEqual(d['max_hint_level'], 'H0')

    def test_clarification_not_technical_failure(self):
        d = make_decision('CLARIFY')
        self.assertEqual(d['authorized_action'], 'CLARIFY')
        self.assertIn('NEEDS_CLARIFICATION', d['hypotheses'])

    def test_test_action_without_receipt_not_verified(self):
        self.assertEqual(make_decision('TEST')['authorized_action'], 'REQUEST_TEST')

    def test_deadline_freezes_before_help(self):
        d = make_decision('HELP', seconds=0)
        self.assertEqual(d['authorized_action'], 'CLOSE')

    def test_closed_does_not_generate_interviewer_question(self):
        d = make_decision('IMPLEMENT', phase='CLOSED')
        self.assertEqual(d['authorized_action'], 'CLOSE')

    def test_boolean_time_hints_rejected(self):
        o = make_obs()
        for name, value in [('time_left_seconds', False), ('hints_used', True)]:
            kwargs = {'observation': o, 'phase': 'INTERVIEWING', 'time_left_seconds': 10,
                      'mechanism': 'STRICT_CHALLENGING', name: value}
            with self.subTest(name=name), self.assertRaises(EvidenceContractError):
                decide_turn(**kwargs)

    def test_hint_ladder_requires_new_human_approved_policy(self):
        with self.assertRaisesRegex(EvidenceContractError, 'HINT_POLICY_NOT_AUTHORIZED'):
            decide_turn(observation=make_obs(kind='HELP'), phase='INTERVIEWING',
                        time_left_seconds=100, mechanism='PROFESSIONAL_SUPPORTIVE', hints_used=1)

    def test_no_unknown_extra_authority_fields(self):
        o = make_obs()
        o['score'] = 100
        with self.assertRaises(EvidenceContractError):
            decide_turn(observation=o, phase='INTERVIEWING', time_left_seconds=50,
                        mechanism='STRICT_CHALLENGING')

    def test_no_raw_candidate_code_in_projected_evidence(self):
        o = make_obs(body='SENTINEL_PRIVATE_CODE_1234 SELECT * FROM secret;')
        self.assertNotIn('SENTINEL_PRIVATE_CODE_1234', json.dumps(o))
        self.assertFalse(o['candidate_text_stored'])

    def test_duplicate_host_event_ids_rejected(self):
        with self.assertRaisesRegex(EvidenceContractError, 'EVENT_NOT_HOST_OWNED'):
            make_obs(known=('candidate-01', 'candidate-01'))

    def test_unknown_candidate_event_not_promoted(self):
        with self.assertRaisesRegex(EvidenceContractError, 'EVENT_NOT_HOST_OWNED'):
            make_obs(known=('candidate-02',))

    def test_unrecognized_event_fields_rejected(self):
        with self.assertRaises(EvidenceContractError):
            project_observation(event={'event_id': 'candidate-01', 'kind': 'IMPLEMENT', 'text': 'abc', 'score': 100},
                                known_event_ids=('candidate-01',), question_sha256=SHA,
                                question_environment='POSTGRESQL')

    def test_stale_or_cross_question_receipt_denied(self):
        with self.assertRaisesRegex(EvidenceContractError, 'CROSS_QUESTION_OR_EVENT_RECEIPT'):
            make_obs(receipt='local-fixture-01', registry=(make_receipt(question_sha=OTHER_SHA),))

    def test_cross_event_receipt_denied(self):
        with self.assertRaisesRegex(EvidenceContractError, 'CROSS_QUESTION_OR_EVENT_RECEIPT'):
            make_obs(receipt='local-fixture-01', registry=(make_receipt(eid='candidate-02'),))

    def test_unrecognized_fake_receipt_cannot_certify_pass(self):
        with self.assertRaisesRegex(EvidenceContractError, 'RECEIPT_NOT_HOST_OWNED'):
            make_obs(receipt='fake-fixture-02')

    def test_duplicate_receipt_registry_ambiguous(self):
        with self.assertRaisesRegex(EvidenceContractError, 'RECEIPT_NOT_HOST_OWNED'):
            make_obs(receipt='local-fixture-01', registry=(make_receipt(), make_receipt()))

    def test_forged_standalone_observation_does_not_verify_fixture(self):
        forged = make_obs()
        forged['execution_receipt_ref'] = 'local-fixture-01'
        forged['execution_status'] = 'PASSED'
        with self.assertRaisesRegex(EvidenceContractError, 'RECEIPT_NOT_HOST_OWNED'):
            decide_turn(observation=forged, phase='INTERVIEWING',
                        time_left_seconds=500, mechanism='STRICT_CHALLENGING')

    def test_private_fields_disallowed_in_public_packet(self):
        d = make_decision()
        with self.assertRaisesRegex(EvidenceContractError, 'PRIVATE_OR_UNKNOWN_QUESTION_FIELD'):
            public_interviewer_packet(decision=d, expected_question_sha256=SHA,
                public_question={'question_id':'Q1', 'question_sha256':SHA, 'environment':'POSTGRESQL',
                    'statement':'Count rows', 'reference_solution':'SELECT private'})

    def test_public_question_sha_binding(self):
        d = make_decision()
        with self.assertRaisesRegex(EvidenceContractError, 'QUESTION_MISMATCH'):
            public_interviewer_packet(decision=d, expected_question_sha256=SHA,
                public_question={'question_id':'Q1', 'question_sha256':OTHER_SHA,
                    'environment':'POSTGRESQL', 'statement':'Count rows'})

    def test_public_packet_contains_only_allowed_inputs(self):
        d = make_decision()
        pkt = public_interviewer_packet(decision=d, expected_question_sha256=SHA,
            public_question={'question_id':'Q1', 'question_sha256':SHA,
                             'environment':'POSTGRESQL', 'statement':'Count rows'})
        self.assertEqual(set(pkt), {'schema', 'question', 'decision'})
        self.assertNotIn('reference_solution', json.dumps(pkt))
        self.assertNotIn('SENTINEL_PRIVATE_CODE', json.dumps(pkt))

    def test_model_reply_cannot_inject_score_or_change_action(self):
        d = make_decision()
        p = dict(d, candidate_facing_reply='What test case would you run?')
        p['score'] = 100
        with self.assertRaises(EvidenceContractError):
            validate_model_reply(decision=d, proposal=p)
        p.pop('score')
        p['authorized_action'] = 'REVEAL_REFERENCE'
        with self.assertRaises(EvidenceContractError):
            validate_model_reply(decision=d, proposal=p)

    def test_model_reply_cannot_change_receipt_binding(self):
        d = make_decision()
        p = dict(d, candidate_facing_reply='Which edge case?')
        p['execution_receipt_ref'] = 'fake'
        with self.assertRaises(EvidenceContractError):
            validate_model_reply(decision=d, proposal=p)

    def test_no_executable_code_block_in_model_reply(self):
        d = make_decision()
        p = dict(d, candidate_facing_reply='```sql\nSELECT * FROM secret\n```')
        with self.assertRaises(EvidenceContractError):
            validate_model_reply(decision=d, proposal=p)

    def test_bounded_reply_and_permitted_model_wording(self):
        d = make_decision()
        good = dict(d, candidate_facing_reply='What single edge case would you test first?')
        self.assertEqual(validate_model_reply(decision=d, proposal=good)['candidate_facing_reply'], good['candidate_facing_reply'])
        good['candidate_facing_reply'] = 'x' * 601
        with self.assertRaises(EvidenceContractError):
            validate_model_reply(decision=d, proposal=good)

    def test_common_three_turn_trajectory(self):
        actions = [('CLARIFY', 'CLARIFY'), ('PLAN', 'REQUEST_INVARIANT'),
                   ('IMPLEMENT', 'REQUEST_TEST')]
        observed = []
        for i, (kind, expected) in enumerate(actions):
            eid = f'candidate-{i+1:02d}'
            o = make_obs(kind, eid=eid, known=tuple(f'candidate-{j+1:02d}' for j in range(i + 1)))
            d = decide_turn(observation=o, phase='INTERVIEWING', time_left_seconds=600-30*i,
                            mechanism='STRICT_CHALLENGING')
            self.assertEqual(d['authorized_action'], expected)
            self.assertEqual(d['evidence_refs'], [eid])
            observed.append(d)
        self.assertEqual(len(observed), 3)

    def test_valid_alternative_three_turn_trajectory(self):
        # Does not label the implementation wrong merely because it differs
        # from an unstated/prepared canonical solution.
        first = make_obs('PLAN', body='Use MIN date plus join for the same goal')
        d1 = decide_turn(observation=first, phase='INTERVIEWING',
                         time_left_seconds=600, mechanism='STRICT_CHALLENGING')
        second = make_obs('IMPLEMENT', body='SELECT id FROM foo')
        d2 = decide_turn(observation=second, phase='INTERVIEWING',
                         time_left_seconds=580, mechanism='STRICT_CHALLENGING')
        third = make_obs('TEST', body='I tried an approved fixture',
                         receipt='local-fixture-01', registry=(make_receipt(),))
        d3 = decide_turn(observation=third, phase='INTERVIEWING',
                         time_left_seconds=560, mechanism='STRICT_CHALLENGING',
                         host_receipts=(make_receipt(),))
        self.assertEqual([x['authorized_action'] for x in (d1,d2,d3)],
                         ['REQUEST_INVARIANT','REQUEST_TEST','REQUEST_EXPLANATION'])
        self.assertNotIn('PASSED_ALL', json.dumps(d3))

    def test_invalid_alternative_three_turn_trajectory(self):
        sequence = [make_obs('PLAN', body='Try a different grouping'),
                    make_obs('IMPLEMENT', body='SELECT count(*) FROM foo'),
                    make_obs('TEST', body='Fixture reported mismatch',
                             receipt='local-fixture-01', registry=(make_receipt('FAILED'),))]
        decisions = [decide_turn(observation=o, phase='INTERVIEWING',
                                 time_left_seconds=450-i*20,
                                 mechanism='PROFESSIONAL_SUPPORTIVE',
                                 host_receipts=(make_receipt('FAILED'),) if i == 2 else ())
                     for i,o in enumerate(sequence)]
        self.assertEqual([x['authorized_action'] for x in decisions],
                         ['REQUEST_INVARIANT','REQUEST_TEST','REQUEST_COUNTEREXAMPLE'])
        self.assertNotIn('STRUCTURAL_GAP', decisions[2]['hypotheses'])

    def test_pandas_observation_follows_same_permission_gate(self):
        o = make_obs('IMPLEMENT', body='df.groupby("id").size()', environment='PANDAS')
        d = decide_turn(observation=o, phase='INTERVIEWING',
                        time_left_seconds=500, mechanism='STRICT_CHALLENGING')
        self.assertEqual(d['authorized_action'], 'REQUEST_TEST')
        self.assertEqual(o['execution_status'], 'NOT_VERIFIED')

    def test_empty_or_oversized_candidate_text_rejected(self):
        for body in ('  ', '😀' * 4096):
            with self.subTest(body_length=len(body)), self.assertRaises(EvidenceContractError):
                make_obs(body=body)

    def test_deterministic_for_replay(self):
        self.assertEqual(make_decision(), make_decision())
        self.assertEqual(json.dumps(make_decision(), sort_keys=True), json.dumps(make_decision(), sort_keys=True))


if __name__ == '__main__':
    unittest.main()
