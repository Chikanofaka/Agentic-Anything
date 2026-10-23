"""E4-C2B2B: narrow, read-only binding of a prior SQL implementation to
one Host-journalled, human-approved, ephemeral PostgreSQL fixture result.

No evaluator runs here. No expected rows, fixtures, candidate SQL, model answer,
or secret Preparer material are included in returned evidence. The Host must
supply the *current* question/index, its most recent candidate implementation,
and its own recorded grade (never a renderer/model-supplied claim).
"""
from __future__ import annotations

import hashlib
import re
from typing import Mapping

from .trajectory_evidence import EvidenceContractError

SHA = re.compile(r'[0-9a-f]{64}\Z')
EVENT_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z')
ALLOWED = {'PASSED', 'FAILED', 'EXECUTION_ERROR'}


def bind_local_sql_fixture(*, question_sha256: str, question_index: int,
                           implementation: Mapping[str, object],
                           candidate_ids: tuple[str, ...],
                           grade: Mapping[str, object]) -> dict:
    """Validate all four source anchors and return a bounded C2A receipt.

    This supplements the already executed/verified Host `grade_execute` path.
    It cannot turn free text or an arbitrary JSON fixture into an execution.
    """
    if (type(question_sha256) is not str or not SHA.fullmatch(question_sha256)
            or type(question_index) is not int or question_index not in (0, 1, 2)
            or type(candidate_ids) is not tuple or len(set(candidate_ids)) != len(candidate_ids)
            or not isinstance(implementation, Mapping)
            or set(implementation) != {'id', 'kind', 'payload'}
            or implementation.get('kind') != 'implement'
            or not isinstance(implementation.get('payload'), Mapping)
            or set(implementation['payload']) != {'text'}):
        raise EvidenceContractError('LOCAL_FIXTURE_EVENT_BINDING')
    event_id = implementation['id']
    code = implementation['payload']['text']
    if (type(event_id) is not str or not EVENT_ID.fullmatch(event_id)
            or type(code) is not str or not code.strip()
            or len(code.encode('utf-8')) > 8192
            or not candidate_ids or candidate_ids[-1] == event_id
            or event_id not in candidate_ids):
        # The candidate must already have produced a separate follow-up event;
        # cannot use fixture data to certify the current, unevaluated input.
        raise EvidenceContractError('LOCAL_FIXTURE_STALE_OR_MISSING_EVENT')
    if not isinstance(grade, Mapping):
        raise EvidenceContractError('LOCAL_FIXTURE_NOT_HOST_OWNED')
    verdict = grade.get('result')
    if (not isinstance(verdict, Mapping)
            or type(verdict.get('status')) is not str
            or verdict['status'] not in ALLOWED
            or type(grade.get('candidate_event_id')) is not str
            or grade['candidate_event_id'] != event_id
            or type(grade.get('question_index')) is not int
            or grade['question_index'] != question_index
            or grade.get('question_sha256') != question_sha256
            or grade.get('source') != 'EPHEMERAL_POSTGRESQL_LOCAL'
            or grade.get('correctness') != 'VERIFIED_LOCAL_FIXTURE'
            or grade.get('official_hidden_tests') is not False
            or grade.get('total_approved_fixtures') != 1
            or type(grade.get('passed_fixtures')) is not int
            or grade['passed_fixtures'] != (1 if verdict['status'] == 'PASSED' else 0)
            or type(grade.get('fixture_sha256')) is not str
            or not SHA.fullmatch(grade['fixture_sha256'])
            or type(grade.get('candidate_sql_sha256')) is not str
            or grade['candidate_sql_sha256'] != hashlib.sha256(code.encode('utf-8')).hexdigest()):
        raise EvidenceContractError('LOCAL_FIXTURE_GRADE_MISMATCH')
    # IDs do not expose candidate code or fixture expected rows.
    evidence_digest = hashlib.sha256(('E4C2B2B\0' + question_sha256 + '\0'
                                     + event_id + '\0' + grade['candidate_sql_sha256']
                                     + '\0' + grade['fixture_sha256']).encode()).hexdigest()
    return {'receipt_id': 'localpg-' + evidence_digest,
            'question_sha256': question_sha256,
            'candidate_event_id': event_id,
            'result': ('ERROR' if verdict['status'] == 'EXECUTION_ERROR' else verdict['status'])}
