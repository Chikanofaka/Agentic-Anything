"""E4D-02C1A: local synthetic bridge demo, no saved interview read or provider call."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tia_runtime.evaluator_v1_host_source import (
    compile_host_source, prepare_host_only_packet, review_untrusted_proposal_json,
)
from tia_runtime.evaluator_v1_semantic_contract import DIMENSIONS, PROPOSAL_SCHEMA


def event(i, kind, text):
    return {'id': f'synthetic-q1:{i}', 'actor': 'candidate', 'kind': kind,
            'payload': {'text': text}}

plan = {
    'status': 'COMPLETE',
    'questions': [{'title': f'Synthetic SQL Question {i+1}', 'content_sha256': str(i+1)*64} for i in range(3)],
    'results': [
        {'index': 0, 'outcome': 'SUBMITTED_UNVERIFIED', 'question_sha256': '1'*64,
         'session': {'events': [event(3, 'clarify', 'Can a customer have two orders on the same day?'),
                                event(5, 'plan', 'I would group by customer and then join on the minimum date.')]}},
        {'index': 1, 'outcome': 'SKIPPED', 'question_sha256': '2'*64, 'session': None},
        {'index': 2, 'outcome': 'SKIPPED', 'question_sha256': '3'*64, 'session': None},
    ]
}
journal = [{'action': 'setup_question_confirm', 'question': 0},
           {'action': 'rehearsal_submit', 'question': 0},
           {'action': 'rehearsal_skip', 'question': 1},
           {'action': 'rehearsal_skip', 'question': 2}]

prepared = prepare_host_only_packet(plan, journal, 0, 'VALID_ALTERNATIVE_UNVERIFIED')
source = prepared['source']
proposal = {'schema': PROPOSAL_SCHEMA, 'role': 'evaluator',
            'source_sha256': source['source_sha256'],
            'dimensions': [{'id': dim, 'anchor': 2 if dim == 'T2' else None,
                            'evidence_ids': ['synthetic-q1:5'] if dim == 'T2' else [],
                            'reason': 'Synthetic example proposed one cited strategy only.' if dim == 'T2' else 'Not observed in this synthetic example.',
                            'confidence': 'LOW' if dim == 'T2' else 'NOT_ASSESSED'} for dim in DIMENSIONS],
            'summary': 'Demonstration only, no real candidate assessment, no model call.'}
review = review_untrusted_proposal_json(plan, journal, source, json.dumps(proposal))
print(json.dumps({
    'stage': 'E4D-02C1A',
    'scenario': source['scenario'],
    'source_events': len(source['evidence']),
    'source_sha256': source['source_sha256'],
    'review_status': review['status'],
    'dimension_count': len(review['dimensions']),
    'cited_dimensions': sum(d['proposed_anchor'] is not None for d in review['dimensions']),
    'verified_score': review['overall_score'],
    'native_request_authorized': prepared['can_submit_provider_request'],
    'actual_paid_requests': prepared['paid_calls'],
    'real_candidate_data_used': False,
}, indent=2))
