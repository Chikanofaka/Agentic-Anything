"""Safe off-line 12-dimension transaction demo (zero actual paid requests)."""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tia_runtime.evaluator_v1_native_transaction import OfflineEvaluatorTransactionHarness
from tia_runtime.evaluator_v1_semantic_contract import DIMENSIONS, PROPOSAL_SCHEMA

def sample():
    plan={'status':'COMPLETE', 'questions':[{'title':f'Demo question {i}', 'content_sha256':str(i+1)*64} for i in range(3)],
          'results':[{'index':i,'outcome':'SUBMITTED_UNVERIFIED','question_sha256':str(i+1)*64,
            'session':{'events':[{'id':f'demo-q{i}:3','actor':'candidate','kind':'plan','payload':{'text':'My approach is to use a window function.'}}]}} for i in range(3)]}
    return plan,[{'action':'rehearsal_complete','seq':1}]

plan,journal=sample();h=OfflineEvaluatorTransactionHarness()
ticket=h.prepare_mock(plan,journal,0,consent=True)
proposal={'schema':PROPOSAL_SCHEMA,'role':'evaluator','source_sha256':ticket['source_sha256'],
          'dimensions':[{'id':k,'anchor':2 if k=='T2' else None,
                         'evidence_ids':['demo-q0:3'] if k=='T2' else [],
                         'reason':'Offline demonstration with a bound candidate event.' if k=='T2' else 'No independently observed rating available.',
                         'confidence':'LOW' if k=='T2' else 'NOT_ASSESSED'} for k in DIMENSIONS],
          'summary':'Synthetic proposal only; it is not a real model evaluation or skill grade.'}
from tia_runtime.evaluator_v1_native_transaction import RECEIPT_SCHEMA, MOCK_TRANSPORT
message={'schema':RECEIPT_SCHEMA, 'role':'evaluator','transport':MOCK_TRANSPORT,
         'transaction_id':ticket['transaction_id'],'request_id':ticket['request_id'],
         'generation':ticket['generation'],'source_sha256':ticket['source_sha256'],
         'proposal_json':json.dumps(proposal)}
response=h.commit_mock(plan,journal,message)
print(json.dumps({'stage':'E4D-02C1B0','role':'evaluator','status':response['status'],
                  'dimensions':len(response['review_packet']['dimensions']),
                  'cited_dimensions':sum(x['proposed_anchor'] is not None for x in response['review_packet']['dimensions']),
                  'verified_competency_score':response['verified_competency_score'],
                  'actual_paid_requests':response['actual_provider_requests'],
                  'native_transport_enabled':h.snapshot()['native_transport_enabled'],
                  'historical_saved_records_mutated':response['persisted_in_host_journal']},indent=2))
