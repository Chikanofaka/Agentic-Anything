"""E4D-02C1B1A: Host-bound Swift local mock wire validation tests."""
from __future__ import annotations
import copy
import json
import unittest
from tia_runtime.evaluator_v1_native_transaction import OfflineEvaluatorTransactionHarness, TransactionError
from tia_runtime.evaluator_v1_native_wire import (
    wire_request, mock_wire_response, wire_to_host_envelope, commit_from_native_wire,
    WireError, RESPONSE_SCHEMA,
)
from tia_runtime.evaluator_v1_semantic_contract import DIMENSIONS, PROPOSAL_SCHEMA


def plan_and_journal():
    p={'status':'COMPLETE', 'questions':[{'title':f'Synthetic {i}', 'content_sha256':str(i+1)*64} for i in range(3)],
       'results':[{'index':i, 'outcome':'SUBMITTED_UNVERIFIED','question_sha256':str(i+1)*64,
         'session':{'events':[{'id':f'demo-q{i}:3','actor':'candidate','kind':'plan','payload':{'text':'A synthetic approach.'}}]}} for i in range(3)]}
    return p,[{'action':'rehearsal_complete','seq':1}]


def proposal(t):
    return {'schema':PROPOSAL_SCHEMA, 'role':'evaluator','source_sha256':t['source_sha256'],
            'dimensions':[{'id':name, 'anchor':2 if name=='T2' else None,
             'evidence_ids':['demo-q0:3'] if name=='T2' else [],
             'reason':'Synthetic reason with a real bound event.' if name=='T2' else 'No independently observed rating.',
             'confidence':'LOW' if name=='T2' else 'NOT_ASSESSED'} for name in DIMENSIONS],
            'summary':'Synthetic offline proposal, not a real model evaluation.'}


class NativeWireContractTests(unittest.TestCase):
    def setUp(self):
        self.plan,self.journal=plan_and_journal()
        self.h=OfflineEvaluatorTransactionHarness()
        self.ticket=self.h.prepare_mock(self.plan,self.journal,0,consent=True)
        self.reply=mock_wire_response(self.ticket,json.dumps(proposal(self.ticket)))

    def test_request_strips_input_and_key(self):
        r=wire_request(self.ticket)
        self.assertEqual(set(r),{'schema','role','transport','transaction_id','request_id','generation','source_sha256'})
        self.assertNotIn('secret',str(r).lower())
        self.assertNotIn('Synthetic',str(r))

    def test_positive_review_only(self):
        resp=commit_from_native_wire(self.h,self.plan,self.journal,self.ticket,json.dumps(self.reply))
        self.assertEqual(resp['status'],'HUMAN_REVIEW_REQUIRED')
        self.assertEqual(resp['verified_competency_score'],None)
        self.assertEqual(len(resp['review_packet']['dimensions']),12)
        self.assertEqual(resp['actual_provider_requests'],0)

    def test_stale_code_cannot_commit(self):
        changed=copy.deepcopy(self.plan)
        changed['results'][0]['session']['events'][0]['payload']['text']='changed code'
        with self.assertRaises(TransactionError):commit_from_native_wire(self.h,changed,self.journal,self.ticket,json.dumps(self.reply))

    def test_wrong_transaction_rejected(self):
        for key in ('transaction_id','request_id','generation','source_sha256'):
            r=copy.deepcopy(self.reply);r[key]='bad' if key!='source_sha256' else '0'*64
            with self.subTest(key=key),self.assertRaises(WireError):wire_to_host_envelope(self.ticket,json.dumps(r))

    def test_unknown_response_key_rejected(self):
        r=copy.deepcopy(self.reply);r['grade']=100
        with self.assertRaises(WireError):wire_to_host_envelope(self.ticket,json.dumps(r))

    def test_duplicate_json_rejected(self):
        raw=json.dumps(self.reply)
        raw=raw.replace('"role": "evaluator",', '"role": "evaluator", "role": "evaluator",',1)
        with self.assertRaises(WireError):wire_to_host_envelope(self.ticket,raw)

    def test_nonfinite_rejected(self):
        raw=json.dumps(self.reply).replace('"proposal_json":', '"unexpected": NaN, "proposal_json":')
        with self.assertRaises(WireError):wire_to_host_envelope(self.ticket,raw)

    def test_unscored_after_bad_citation(self):
        p=proposal(self.ticket);p['dimensions'][1]['evidence_ids']=['fake-id']
        r=mock_wire_response(self.ticket,json.dumps(p))
        with self.assertRaises(TransactionError):commit_from_native_wire(self.h,self.plan,self.journal,self.ticket,json.dumps(r))
        self.assertEqual(self.h.snapshot()['real_grade'],None)

    def test_cancellation_rejects_late_native_reply(self):
        self.h.cancel_mock()
        with self.assertRaises(TransactionError):commit_from_native_wire(self.h,self.plan,self.journal,self.ticket,json.dumps(self.reply))

    def test_recovery_rejects_late_native_reply(self):
        self.h.simulate_recovery()
        with self.assertRaises(TransactionError):commit_from_native_wire(self.h,self.plan,self.journal,self.ticket,json.dumps(self.reply))

    def test_duplicate_success_rejected(self):
        commit_from_native_wire(self.h,self.plan,self.journal,self.ticket,json.dumps(self.reply))
        with self.assertRaises(TransactionError):commit_from_native_wire(self.h,self.plan,self.journal,self.ticket,json.dumps(self.reply))

    def test_boolean_paid_flag_cannot_grant_authority(self):
        for fld in ('paid_consent_granted','native_request_authorized'):
            r=copy.deepcopy(self.ticket);r[fld]=1
            with self.subTest(field=fld),self.assertRaises(WireError):wire_request(r)

    def test_wrong_role_or_transport_rejected(self):
        for field, value in [('role','trainer'),('transport','LIVE_OPENAI'),('status','COMPLETE')]:
            r=copy.deepcopy(self.ticket);r[field]=value
            with self.subTest(field=field),self.assertRaises(WireError):wire_request(r)

    def test_invalid_ids_rejected(self):
        for field in ('transaction_id','request_id','generation'):
            t=copy.deepcopy(self.ticket);t[field]='A'*120
            with self.subTest(field=field),self.assertRaises(WireError):wire_request(t)

    def test_size_limit(self):
        r=copy.deepcopy(self.reply);r['proposal_json']='a'*32769
        with self.assertRaises(WireError):wire_to_host_envelope(self.ticket,json.dumps(r))

    def test_no_production_native_authority(self):
        r=wire_request(self.ticket)
        self.assertNotIn('native_request_authorized',r)
        self.assertEqual(r['transport'],'LOCAL_LOOPBACK_MOCK_HTTP')
        self.assertNotIn('https:',json.dumps(r))

if __name__=='__main__':unittest.main()
