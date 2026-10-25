"""Offline exemplar: emits source-bound semantic proposal, no API call."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tia_runtime.evaluator_v1_semantic_contract import (
    DIMENSIONS, PROPOSAL_SCHEMA, build_review_packet, compile_source)

sha = lambda text: hashlib.sha256(text.encode('utf-8')).hexdigest()
excerpt = 'I used a window function to compute the running sum ordered by turn.'
source = compile_source('1'*64, 2, [
    {'id': 'session-q3:1', 'question_index': 2, 'actor': 'candidate',
     'kind': 'plan', 'excerpt': excerpt, 'excerpt_sha256': sha(excerpt)}],
    'COMMON_PATH', '2'*64)
dimensions = [{'id': key, 'anchor': 3 if key == 'T2' else None,
               'evidence_ids': ['session-q3:1'] if key == 'T2' else [],
               'reason': 'Candidate described an ordering and cumulative sum.' if key == 'T2' else 'Not observed in this short scenario.',
               'confidence': 'LOW' if key == 'T2' else 'NOT_ASSESSED'} for key in DIMENSIONS]
proposal = {'schema': PROPOSAL_SCHEMA, 'role': 'evaluator',
            'source_sha256': source['source_sha256'], 'dimensions': dimensions,
            'summary': 'Illustrative proposal, with one cited dimension and eleven unobserved.'}
print(json.dumps(build_review_packet(source, proposal), indent=2, ensure_ascii=False))
