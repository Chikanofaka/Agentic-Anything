"""E4-C2A: deterministic, read-only evidence projection; never a scorer.

Host passes its *own* event identifiers and independent execution receipt registry.
This module never infers correctness from candidate or model text, requests an
executor, loads the preparer's secret vault, or mutates the interview journal.
"""
from __future__ import annotations

import re
from typing import Mapping

SCHEMA = 'tia-turn-observation/v1'
ACTIONS = {'CLARIFY', 'PLAN', 'IMPLEMENT', 'TEST', 'HELP'}
ENVIRONMENTS = {'POSTGRESQL', 'PANDAS'}
RECEIPT_RESULTS = {'PASSED', 'FAILED', 'ERROR', 'NOT_VERIFIED'}
_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$')
_SHA = re.compile(r'^[0-9a-f]{64}$')


class EvidenceContractError(ValueError):
    """Untrusted observation or provenance does not meet the Host contract."""


def _exact(value: object, typ: type) -> bool:
    return type(value) is typ


def _id(value: object) -> bool:
    return _exact(value, str) and bool(_ID.fullmatch(value))


def _sha(value: object) -> bool:
    return _exact(value, str) and bool(_SHA.fullmatch(value))


def project_observation(*, event: Mapping[str, object], known_event_ids: tuple[str, ...],
                        question_sha256: str, question_environment: str,
                        receipt_ref: str | None = None,
                        host_receipts: tuple[Mapping[str, object], ...] = ()) -> dict:
    """Return nonsecret observation and one independently anchored receipt status.

    A text string saying 'passed' has NO authority. Receipt IDs are only trusted
    when found in the Host-supplied independent receipt registry and bound to
    exactly this question/event. The original code/text is never in output.
    """
    if not _sha(question_sha256) or type(question_environment) is not str or question_environment not in ENVIRONMENTS:
        raise EvidenceContractError('INVALID_QUESTION_BINDING')
    if not isinstance(event, Mapping) or set(event) != {'event_id', 'kind', 'text'}:
        raise EvidenceContractError('INVALID_EVENT_SCHEMA')
    eid, action, body = event['event_id'], event['kind'], event['text']
    if not _id(eid) or not _exact(action, str) or action not in ACTIONS:
        raise EvidenceContractError('INVALID_EVENT_ACTION')
    if type(known_event_ids) is not tuple or not known_event_ids or any(not _id(e) for e in known_event_ids):
        raise EvidenceContractError('INVALID_HOST_EVENT_REGISTRY')
    if len(set(known_event_ids)) != len(known_event_ids) or eid not in known_event_ids:
        raise EvidenceContractError('EVENT_NOT_HOST_OWNED')
    if not _exact(body, str) or not body.strip() or len(body.encode('utf-8')) > 8192:
        raise EvidenceContractError('INVALID_EVENT_TEXT')
    if type(host_receipts) is not tuple:
        raise EvidenceContractError('INVALID_HOST_RECEIPT_REGISTRY')
    result = 'NOT_VERIFIED'
    if receipt_ref is not None:
        if not _id(receipt_ref):
            raise EvidenceContractError('INVALID_RECEIPT_REF')
        hits = [r for r in host_receipts if isinstance(r, Mapping) and r.get('receipt_id') == receipt_ref]
        if len(hits) != 1:
            raise EvidenceContractError('RECEIPT_NOT_HOST_OWNED')
        receipt = hits[0]
        if set(receipt) != {'receipt_id', 'question_sha256', 'candidate_event_id', 'result'}:
            raise EvidenceContractError('INVALID_RECEIPT_SCHEMA')
        if receipt['question_sha256'] != question_sha256 or receipt['candidate_event_id'] != eid:
            raise EvidenceContractError('CROSS_QUESTION_OR_EVENT_RECEIPT')
        if not _exact(receipt['result'], str) or receipt['result'] not in RECEIPT_RESULTS:
            raise EvidenceContractError('UNTRUSTED_EXECUTION_STATUS')
        result = receipt['result']
    return {'schema': SCHEMA, 'question_sha256': question_sha256,
            'question_environment': question_environment, 'candidate_event_ids': [eid],
            'observed_action': action, 'execution_receipt_ref': receipt_ref,
            'execution_status': result, 'candidate_text_stored': False}
