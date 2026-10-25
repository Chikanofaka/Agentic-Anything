"""Offline-only E4D-02C1B0 protocol abuse and recovery checks."""
import copy
import json
import unittest
from unittest.mock import patch
from tia_runtime.evaluator_v1_native_transaction import (
    OfflineEvaluatorTransactionHarness, TransactionError, TX_SCHEMA,
    RECEIPT_SCHEMA, MOCK_TRANSPORT,
)
from tia_runtime.evaluator_v1_semantic_contract import DIMENSIONS, PROPOSAL_SCHEMA
from tia_runtime.evaluator_v1_host_source import compile_host_source


def fixture():
    questions = [{'title':f'Fake Q{i}', 'content_sha256':str(i+1)*64} for i in range(3)]
    results=[]
    for i in range(3):
        results.append({'index':i, 'question_sha256':str(i+1)*64, 'outcome':'SUBMITTED_UNVERIFIED',
                        'session':{'events':[{'id':f'sim-q{i}:3', 'actor':'candidate',
                          'kind':'plan','payload':{'text':'I would use a grouped approach.'}},
                         {'id':f'sim-q{i}:4','actor':'candidate','kind':'implement',
                          'payload':{'text':'SELECT 42;'}}]}})
    return ({'status':'COMPLETE', 'questions':questions, 'results':results},
            [{'action':'rehearsal_start', 'step':1}, {'action':'rehearsal_submit', 'step':2}])


def model_reply(plan,journal,index):
    src=compile_host_source(plan,journal,index)
    return {'schema':PROPOSAL_SCHEMA, 'role':'evaluator', 'source_sha256':src['source_sha256'],
            'dimensions':[{'id':dim, 'anchor':2 if dim=='T2' else None,
                           'evidence_ids':[f'sim-q{index}:3'] if dim=='T2' else [],
                           'reason':'Synthetic source-limited evaluation; no actual AI model.' if dim=='T2' else 'No relevant verified evidence exists.',
                           'confidence':'LOW' if dim=='T2' else 'NOT_ASSESSED'} for dim in DIMENSIONS],
            'summary':'Mock HTTP contract simulation. No model call or scoring authority.'}


def envelope(ticket,proposal):
    return {'schema':RECEIPT_SCHEMA,'role':'evaluator','transport':MOCK_TRANSPORT,
            'transaction_id':ticket['transaction_id'], 'request_id':ticket['request_id'],
            'generation':ticket['generation'], 'source_sha256':ticket['source_sha256'],
            'proposal_json':json.dumps(proposal,sort_keys=True)}


class TransactionContractTests(unittest.TestCase):
    def setUp(self):
        self.plan,self.journal=fixture()
        self.host=OfflineEvaluatorTransactionHarness()
        self.original=copy.deepcopy((self.plan,self.journal))

    def start(self,index=0):
        return self.host.prepare_mock(self.plan,self.journal,index,consent=True)

    def reply(self,index=0,ticket=None):
        ticket=ticket or self.start(index)
        return envelope(ticket,model_reply(self.plan,self.journal,index))

    def assert_rejected(self,code,fn,*args,**kwargs):
        with self.assertRaises(TransactionError) as caught:
            fn(*args,**kwargs)
        self.assertEqual(caught.exception.code,code)

    def test_success_is_review_not_score(self):
        packet=self.host.commit_mock(self.plan,self.journal,self.reply())
        self.assertEqual(packet['status'],'HUMAN_REVIEW_REQUIRED')
        self.assertEqual(packet['review_packet']['status'],'HUMAN_REVIEW_REQUIRED')
        self.assertIsNone(packet['verified_competency_score'])
        self.assertIsNone(packet['review_packet']['overall_score'])

    def test_one_citation_twelve_dimensions(self):
        packet=self.host.commit_mock(self.plan,self.journal,self.reply())['review_packet']
        self.assertEqual(len(packet['dimensions']),12)
        only=[d for d in packet['dimensions'] if d['proposed_anchor'] is not None]
        self.assertEqual(len(only),1)
        self.assertEqual(only[0]['evidence'][0]['event_id'],'sim-q0:3')

    def test_no_paid_calls_before_or_after(self):
        ticket=self.start()
        self.assertEqual(ticket['real_provider_calls'],0)
        self.assertFalse(ticket['native_request_authorized'])
        self.host.commit_mock(self.plan,self.journal,self.reply(ticket=ticket))
        self.assertEqual(self.host.snapshot()['actual_provider_requests'],0)
        self.assertEqual(self.host.snapshot()['mock_requests'],1)

    def test_does_not_change_plan_journal(self):
        self.host.commit_mock(self.plan,self.journal,self.reply())
        self.assertEqual((self.plan,self.journal),self.original)

    def test_no_consent_fails(self):
        self.assert_rejected('EXPLICIT_MOCK_CONSENT_REQUIRED',self.host.prepare_mock,self.plan,self.journal,0,consent=False)

    def test_truthiness_cannot_grant_consent(self):
        self.assert_rejected('EXPLICIT_MOCK_CONSENT_REQUIRED',self.host.prepare_mock,self.plan,self.journal,0,consent=1)

    def test_live_transport_explicitly_blocked(self):
        self.assert_rejected('LIVE_NATIVE_TRANSPORT_NOT_IMPLEMENTED',self.host.prepare_mock,self.plan,self.journal,0,consent=True,transport='LIVE_OPENAI')

    def test_pending_blocks_parallel(self):
        self.start()
        self.assert_rejected('EVALUATOR_TRANSACTION_ALREADY_PENDING',self.host.prepare_mock,self.plan,self.journal,1,consent=True)

    def test_second_question_after_success(self):
        self.host.commit_mock(self.plan,self.journal,self.reply(0))
        ret=self.host.commit_mock(self.plan,self.journal,self.reply(1))
        self.assertEqual(ret['mock_requests'],2)
        self.assertNotEqual(ret['review_packet']['question_index'],0)

    def test_model_role_spoof_rejected(self):
        r=self.reply();r['role']='interviewer'
        self.assert_rejected('INVALID_MOCK_REPLY_ROLE_OR_TRANSPORT',self.host.commit_mock,self.plan,self.journal,r)

    def test_model_transport_spoof_rejected(self):
        r=self.reply();r['transport']='LIVE_OPENAI'
        self.assert_rejected('INVALID_MOCK_REPLY_ROLE_OR_TRANSPORT',self.host.commit_mock,self.plan,self.journal,r)

    def test_extra_score_field_rejected(self):
        r=self.reply();r['overall_grade']=100
        self.assert_rejected('INVALID_MOCK_REPLY_ENVELOPE',self.host.commit_mock,self.plan,self.journal,r)

    def test_wrong_transaction_id_rejected(self):
        r=self.reply();r['transaction_id']='tx_other'
        self.assert_rejected('REPLY_TRANSACTION_MISMATCH',self.host.commit_mock,self.plan,self.journal,r)

    def test_wrong_request_id_rejected(self):
        r=self.reply();r['request_id']='req_other'
        self.assert_rejected('REPLY_TRANSACTION_MISMATCH',self.host.commit_mock,self.plan,self.journal,r)

    def test_wrong_generation_rejected(self):
        r=self.reply();r['generation']='gen_other'
        self.assert_rejected('REPLY_TRANSACTION_MISMATCH',self.host.commit_mock,self.plan,self.journal,r)

    def test_wrong_sha_rejected(self):
        r=self.reply();r['source_sha256']='a'*64
        self.assert_rejected('REPLY_SOURCE_DIGEST_MISMATCH',self.host.commit_mock,self.plan,self.journal,r)

    def test_stale_candidate_code_rejected(self):
        r=self.reply();self.plan['results'][0]['session']['events'][1]['payload']['text']='SELECT 999;'
        self.assert_rejected('STALE_HOST_EVIDENCE_AT_COMMIT',self.host.commit_mock,self.plan,self.journal,r)

    def test_stale_journal_rejected(self):
        r=self.reply();self.journal.append({'action':'replay','step':3})
        self.assert_rejected('STALE_HOST_EVIDENCE_AT_COMMIT',self.host.commit_mock,self.plan,self.journal,r)

    def test_stale_question_rejected(self):
        r=self.reply();self.plan['questions'][0]['title']='Changed question'
        self.assert_rejected('STALE_HOST_EVIDENCE_AT_COMMIT',self.host.commit_mock,self.plan,self.journal,r)

    def test_duplicate_success_cannot_be_committed(self):
        r=self.reply();self.host.commit_mock(self.plan,self.journal,r)
        self.assert_rejected('NO_PENDING_MOCK_TRANSACTION',self.host.commit_mock,self.plan,self.journal,r)

    def test_cancel_invalidates_old_reply(self):
        r=self.reply();self.host.cancel_mock()
        self.assert_rejected('NO_PENDING_MOCK_TRANSACTION',self.host.commit_mock,self.plan,self.journal,r)
        self.assertEqual(self.host.snapshot()['mock_requests'],0)

    def test_recovery_invalidates_old_reply(self):
        r=self.reply();rec=self.host.simulate_recovery()
        self.assertEqual(rec['status'],'NO_AUTO_RETRY')
        self.assert_rejected('NO_PENDING_MOCK_TRANSACTION',self.host.commit_mock,self.plan,self.journal,r)
        self.assertEqual(self.host.snapshot()['actual_provider_requests'],0)

    def test_recover_does_not_duplicate_request(self):
        self.start();self.host.simulate_recovery()
        self.assertEqual(self.host.snapshot()['mock_requests'],0)
        self.assertFalse(self.host.snapshot()['pending'])

    def test_cancel_when_no_pending_rejected(self):
        self.assert_rejected('NO_PENDING_MOCK_TRANSACTION',self.host.cancel_mock)

    def test_untrusted_model_scores_rejected(self):
        r=self.reply();data=json.loads(r['proposal_json']);data['overall_grade']=100
        r['proposal_json']=json.dumps(data)
        self.assert_rejected('INVALID_UNTRUSTED_MODEL_PROPOSAL_UNTRUSTED_PROPOSAL_REJECTED_INVALID_PROPOSAL_SHAPE',self.host.commit_mock,self.plan,self.journal,r)

    def test_nonfinite_reply_rejected(self):
        r=self.reply();r['proposal_json']=r['proposal_json'].replace('"anchor": 2','"anchor": NaN')
        self.assert_rejected('INVALID_UNTRUSTED_MODEL_PROPOSAL_UNTRUSTED_PROPOSAL_REJECTED_NONFINITE_JSON_VALUE',self.host.commit_mock,self.plan,self.journal,r)

    def test_missing_citation_rejected(self):
        r=self.reply();data=json.loads(r['proposal_json']);data['dimensions'][2]['anchor']=4
        r['proposal_json']=json.dumps(data)
        self.assert_rejected('INVALID_UNTRUSTED_MODEL_PROPOSAL_UNTRUSTED_PROPOSAL_REJECTED_UNCITED_OR_UNCALIBRATED_ANCHOR',self.host.commit_mock,self.plan,self.journal,r)

    def test_open_rehearsal_rejected(self):
        self.plan['status']='ACTIVE'
        self.assert_rejected('HOST_SOURCE_REJECTED_REHEARSAL_NOT_FROZEN_COMPLETE',self.host.prepare_mock,self.plan,self.journal,0,consent=True)

    def test_duplicate_json_key_rejected(self):
        r=self.reply();r['proposal_json']='{"schema": "x", "schema": "y"}'
        self.assert_rejected('INVALID_UNTRUSTED_MODEL_PROPOSAL_UNTRUSTED_PROPOSAL_REJECTED_DUPLICATE_JSON_KEY',self.host.commit_mock,self.plan,self.journal,r)

    def test_no_sanitized_candidate_code_in_public_snapshot(self):
        self.start()
        self.assertNotIn('SELECT 42;',str(self.host.snapshot()))

    def test_recover_without_pending_is_safe(self):
        result=self.host.simulate_recovery()
        self.assertEqual(result['status'],'NO_AUTO_RETRY')

    def test_concurrent_double_commit_not_possible_in_serial_protocol(self):
        r=self.reply();result=self.host.commit_mock(self.plan,self.journal,r)
        self.assertEqual(result['mock_requests'],1)
        self.assert_rejected('NO_PENDING_MOCK_TRANSACTION',self.host.commit_mock,self.plan,self.journal,r)

    def test_schema_has_native_disabled_flag(self):
        p=self.start();self.assertEqual(p['schema'],TX_SCHEMA)
        self.assertEqual(self.host.snapshot()['native_transport_enabled'],False)

if __name__=='__main__': unittest.main()
