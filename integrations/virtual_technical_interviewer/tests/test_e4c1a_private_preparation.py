"""E4-C1A: deterministic private proposal contract tests. No paid API calls."""
import copy
import json
import unittest
from tia_runtime.setup import InterviewConfig, review_question
from tia_runtime.private_preparation import (
    create_private_binding, validate_preparer_proposal,
    InMemoryReferenceEnvelope, PreparationContractError, PROPOSAL_SCHEMA,
)


def config(n=3, env='POSTGRESQL'):
    return InterviewConfig(technical_environment=env, duration_minutes=45 if n == 3 else 60,
                           difficulty='HARD', question_source='BYOQ',
                           interviewer_mechanism='STRICT_CHALLENGING')


def reviews(n=3, env='POSTGRESQL'):
    out=[]
    for i in range(n):
        f={'problem_statement':f'Problem {i} find max orders', 'task':'Return correct result',
           'schema':'Delivery(order_id INTEGER)', 'example_input':'order_id=1',
           'expected_output':'1', 'environment':env, 'source':'OWNER',
           'source_reference':f'synthetic://q{i}', 'constraints':'one line'}
        q=review_question(f, env)
        assert not q['issues'], q
        q.update(human_confirmed=True, practice_eligible=True)
        out.append(q)
    return out


def proposal(binding):
    return {'schema':PROPOSAL_SCHEMA, 'question_set_sha256':binding['question_set_sha256'],
            'items':[{'question_sha256':q['question_sha256'], 'language':q['environment'],
                      'approaches':[{'label':'aggregation','code':'SELECT max(order_id) FROM Delivery',
                                     'rationale':'Query all rows', 'invariants':['one row'],
                                     'edge_cases':['empty','null'],'complexity':'linear'}]}
                     for q in binding['questions']]}


class PrivatePreparationContracts(unittest.TestCase):
    def test_three_questions_contract(self):
        b=create_private_binding(config(),reviews())
        result=validate_preparer_proposal(b, proposal(b))
        self.assertEqual(len(result['items']),3)
        self.assertEqual(result['code_execution_status'],'NOT_RUN')

    def test_four_questions_contract_not_four_live(self):
        b=create_private_binding(config(4), reviews(4))
        self.assertEqual(len(validate_preparer_proposal(b, proposal(b))['items']),4)

    def test_incomplete_question_review_rejected(self):
        q=reviews();q[0]['human_confirmed']=False
        with self.assertRaises(PreparationContractError):create_private_binding(config(),q)

    def test_duplicate_question_rejected(self):
        q=reviews();q[1]=copy.deepcopy(q[0])
        with self.assertRaises(PreparationContractError):create_private_binding(config(),q)

    def test_modified_question_sha_rejected(self):
        q=reviews();q[1]['content_sha256']='f'*64
        with self.assertRaises(PreparationContractError):create_private_binding(config(),q)

    def test_mismatched_environment_rejected(self):
        q=reviews();q[1]['fields']['environment']='PANDAS'
        with self.assertRaises(PreparationContractError):create_private_binding(config(),q)

    def test_model_cannot_certify_pass(self):
        b=create_private_binding(config(),reviews());p=proposal(b)
        p['items'][0]['approaches'][0]['verification_status']='VERIFIED_LOCAL_FIXTURE'
        with self.assertRaises(PreparationContractError):validate_preparer_proposal(b,p)

    def test_model_cannot_certify_score(self):
        b=create_private_binding(config(),reviews());p=proposal(b);p['score']=99
        with self.assertRaises(PreparationContractError):validate_preparer_proposal(b,p)

    def test_reordered_questions_rejected(self):
        b=create_private_binding(config(),reviews());p=proposal(b)
        p['items'].reverse()
        with self.assertRaises(PreparationContractError):validate_preparer_proposal(b,p)

    def test_shortened_model_response_rejected(self):
        b=create_private_binding(config(),reviews());p=proposal(b)
        p['items'].pop()
        with self.assertRaises(PreparationContractError):validate_preparer_proposal(b,p)

    def test_forged_model_binding_rejected(self):
        b=create_private_binding(config(),reviews());p=proposal(b)
        p['question_set_sha256']='a'*64
        with self.assertRaises(PreparationContractError):validate_preparer_proposal(b,p)

    def test_tampered_binding_rejected(self):
        b=create_private_binding(config(),reviews());p=proposal(b)
        b['questions'][0]['question_sha256']='b'*64
        with self.assertRaises(PreparationContractError):validate_preparer_proposal(b,p)

    def test_sentinel_code_never_appears_in_public_summary(self):
        b=create_private_binding(config(),reviews());p=proposal(b)
        sentinel='SENSITIVE_REFERENCE_SOLUTION'
        p['items'][1]['approaches'][0]['code']=sentinel
        env=InMemoryReferenceEnvelope(b,p)
        self.assertNotIn(sentinel,json.dumps(env.public_status()))
        self.assertNotIn(sentinel,repr(env))
        self.assertFalse(env.public_status()['interviewer_reference_access'])
        self.assertEqual(env.public_status()['technical_score'],'NOT_SCORED')

    def test_interviewer_and_trainer_denied_full_reference(self):
        b=create_private_binding(config(),reviews());env=InMemoryReferenceEnvelope(b,proposal(b))
        for actor,phase in [('interviewer','INTERVIEWING'),('trainer','REVIEWING'),('evaluator','REVIEWING')]:
            with self.subTest(actor=actor):
                with self.assertRaises(PreparationContractError):
                    env.trusted_oracle_only(caller=actor,interview_phase=phase)

    def test_explicit_private_phase_only(self):
        b=create_private_binding(config(),reviews());env=InMemoryReferenceEnvelope(b,proposal(b))
        with self.assertRaises(PreparationContractError):
            env.trusted_oracle_only(caller='oracle',interview_phase='INTERVIEWING')
        priv=env.trusted_oracle_only(caller='oracle',interview_phase='PRIVATE_PREPARATION')
        self.assertEqual(priv['items'][0]['approaches'][0]['verification_status'],'REFERENCE_UNVERIFIED_AI_PROPOSAL')
        priv['items'][0]['approaches'][0]['code']='HACK'
        self.assertNotEqual(env.trusted_oracle_only(caller='oracle',interview_phase='PRIVATE_PREPARATION')['items'][0]['approaches'][0]['code'],'HACK')

    def test_long_code_rejected(self):
        b=create_private_binding(config(),reviews());p=proposal(b)
        p['items'][0]['approaches'][0]['code']='x'*8193
        with self.assertRaises(PreparationContractError):validate_preparer_proposal(b,p)

    def test_non_json_nan_rejected(self):
        b=create_private_binding(config(),reviews());p=proposal(b)
        p['items'][0]['approaches'][0]['complexity']=float('nan')
        with self.assertRaises(PreparationContractError):validate_preparer_proposal(b,p)

    def test_model_cannot_supply_arbitrary_fields(self):
        b=create_private_binding(config(),reviews());p=proposal(b)
        p['items'][0]['approaches'][0]['api_key']='DO_NOT_STORE'
        with self.assertRaises(PreparationContractError):validate_preparer_proposal(b,p)

    def test_invalid_binding_length_rejected(self):
        b=create_private_binding(config(),reviews());p=proposal(b)
        b['questions']=b['questions'][:2]
        with self.assertRaises(PreparationContractError):validate_preparer_proposal(b,p)

    def test_does_not_automatically_execute_or_bill(self):
        b=create_private_binding(config(),reviews());env=InMemoryReferenceEnvelope(b,proposal(b))
        s=env.public_status()
        self.assertEqual(s['status'],'UNVERIFIED_MODEL_PROPOSAL_ONLY')
        self.assertEqual(s['execution_status'],'NOT_RUN')
        self.assertNotIn('api_key',json.dumps(s))


if __name__=='__main__':unittest.main()
