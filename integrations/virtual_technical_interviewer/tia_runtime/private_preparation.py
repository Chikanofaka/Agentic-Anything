"""E4-C1A: private, in-memory *contract* for a future Native BYOK Preparer.

No provider, filesystem, SQL/Pandas execution or Host command is connected here.
Model output is untrusted proposed source material; the reference is NEVER a pass.
This module is not a cryptographic sandbox: C1B must enforce transport/process
and persisted-reference isolation before real remote-model preparation.
"""
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import re

from .preflight_preparer import build_preflight_readiness

BINDING_SCHEMA = 'tia-private-prep-binding/v1'
PROPOSAL_SCHEMA = 'tia-preparer-model-proposal/v1'
PUBLIC_SCHEMA = 'tia-preparer-public-status/v1'
MAX_PROPOSAL_BYTES = 131072
MAX_CODE_BYTES = 8192
_SHA = re.compile(r'[0-9a-f]{64}\Z')
_ALLOWED_LANGUAGES = {'POSTGRESQL', 'PANDAS'}


class PreparationContractError(ValueError):
    """Error code only, with NO private answer/question text."""


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True, allow_nan=False).encode('utf-8')).hexdigest()


def create_private_binding(config, reviews):
    """Derive an exact ordered 3/4-question SHA binding from checked C0 records.

    This has NO question text, code or model-generated values and no authority to
    issue a network request. Existing single-environment setup constraints remain.
    """
    pf = build_preflight_readiness(config, reviews)
    if (pf['status'] != 'READY_FOR_FUTURE_PRIVATE_PREPARATION' or
            pf['required_count'] not in (3, 4) or
            len(pf['questions']) != pf['required_count']):
        raise PreparationContractError('CONFIRMED_QUESTIONS_REQUIRED')
    questions = []
    for pos, q in enumerate(pf['questions']):
        if (q['question_index'] != pos or q['status'] != 'SOURCE_BOUND_CONFIRMED'
                or q['environment'] not in _ALLOWED_LANGUAGES
                or type(q['question_sha256']) is not str or
                _SHA.fullmatch(q['question_sha256']) is None):
            raise PreparationContractError('INVALID_QUESTION_BINDING')
        questions.append({'index': pos, 'question_sha256': q['question_sha256'],
                          'environment': q['environment']})
    if len({q['question_sha256'] for q in questions}) != len(questions):
        raise PreparationContractError('DUPLICATE_QUESTIONS')
    content = {'schema': BINDING_SCHEMA, 'questions': questions}
    return {**content, 'question_set_sha256': _digest(content)}


def _text(value, *, max_bytes, allow_empty=False):
    if type(value) is not str or (not allow_empty and not value.strip()):
        raise PreparationContractError('INVALID_PREPARER_FIELD')
    try:
        if '\x00' in value or len(value.encode('utf-8')) > max_bytes:
            raise PreparationContractError('INVALID_PREPARER_FIELD')
    except UnicodeError:
        raise PreparationContractError('INVALID_PREPARER_FIELD') from None
    return value


def _strings(value, *, cap):
    if type(value) is not list or not 1 <= len(value) <= 6:
        raise PreparationContractError('INVALID_PREPARER_LIST')
    return [_text(x, max_bytes=cap) for x in value]


def validate_preparer_proposal(binding, proposal):
    """Fail-closed schema and exact SHA/language/order validation; NO grading.

    The output may be wrong semantically even if accepted by this validation.
    Crucially, `verified`, scores and oracle pass flags are not allowed in input.
    """
    if type(binding) is not dict or set(binding) != {'schema', 'questions', 'question_set_sha256'}:
        raise PreparationContractError('INVALID_BINDING')
    if binding['schema'] != BINDING_SCHEMA or not isinstance(binding['questions'], list):
        raise PreparationContractError('INVALID_BINDING')
    try:
        expected = _digest({'schema': BINDING_SCHEMA, 'questions': binding['questions']})
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise PreparationContractError('INVALID_BINDING') from None
    if (not hmac.compare_digest(str(binding['question_set_sha256']), expected)
            or len(binding['questions']) not in (3, 4)):
        raise PreparationContractError('INVALID_BINDING')
    canonical_items = []
    for index, q in enumerate(binding['questions']):
        if (type(q) is not dict or set(q) != {'index', 'question_sha256', 'environment'}
                or type(q['index']) is not int or q['index'] != index
                or type(q['question_sha256']) is not str
                or _SHA.fullmatch(q['question_sha256']) is None
                or q['environment'] not in _ALLOWED_LANGUAGES):
            raise PreparationContractError('INVALID_BINDING')
        canonical_items.append(q)
    if len({q['question_sha256'] for q in canonical_items}) != len(canonical_items):
        raise PreparationContractError('INVALID_BINDING')
    if type(proposal) is not dict or set(proposal) != {'schema', 'question_set_sha256', 'items'}:
        raise PreparationContractError('INVALID_PREPARER_PROPOSAL')
    try:
        total = len(json.dumps(proposal, ensure_ascii=False, allow_nan=False).encode('utf-8'))
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise PreparationContractError('INVALID_PREPARER_PROPOSAL') from None
    if total > MAX_PROPOSAL_BYTES or proposal['schema'] != PROPOSAL_SCHEMA:
        raise PreparationContractError('INVALID_PREPARER_PROPOSAL')
    if (type(proposal['question_set_sha256']) is not str or
            not hmac.compare_digest(proposal['question_set_sha256'], expected)):
        raise PreparationContractError('STALE_PREPARER_BINDING')
    if type(proposal['items']) is not list or len(proposal['items']) != len(canonical_items):
        raise PreparationContractError('INCOMPLETE_PREPARER_PROPOSAL')
    validated = []
    for expected_item, item in zip(canonical_items, proposal['items']):
        if (type(item) is not dict or set(item) != {'question_sha256', 'language', 'approaches'}
                or item['question_sha256'] != expected_item['question_sha256']
                or item['language'] != expected_item['environment']):
            raise PreparationContractError('QUESTION_SOURCE_MISMATCH')
        approaches = item['approaches']
        if type(approaches) is not list or not 1 <= len(approaches) <= 3:
            raise PreparationContractError('INVALID_APPROACHES')
        sealed_approaches = []
        for a in approaches:
            if type(a) is not dict or set(a) != {'label', 'code', 'rationale', 'invariants', 'edge_cases', 'complexity'}:
                raise PreparationContractError('INVALID_APPROACHES')
            sealed_approaches.append({
                'label': _text(a['label'], max_bytes=100),
                'code': _text(a['code'], max_bytes=MAX_CODE_BYTES),
                'rationale': _text(a['rationale'], max_bytes=1800),
                'invariants': _strings(a['invariants'], cap=500),
                'edge_cases': _strings(a['edge_cases'], cap=500),
                'complexity': _text(a['complexity'], max_bytes=500),
                # Derived status only; never taken from untrusted model text.
                'verification_status': 'REFERENCE_UNVERIFIED_AI_PROPOSAL',
            })
        validated.append({
            'question_sha256': expected_item['question_sha256'],
            'environment': expected_item['environment'],
            'approaches': sealed_approaches,
        })
    return {'schema': 'tia-sealed-preparation-proposal/v1',
            'question_set_sha256': expected, 'items': validated,
            'code_execution_status': 'NOT_RUN', 'technical_score': 'NOT_SCORED'}


class InMemoryReferenceEnvelope:
    """Pure Python prototype; production trust still needs Native/OS boundary.

    Deliberately NOT inserted into Host state, public snapshot, logs or exports.
    Callers possessing this object are privileged; it is not an OS security vault.
    """
    __slots__ = ('_sealed',)

    def __init__(self, binding, proposal):
        self._sealed = copy.deepcopy(validate_preparer_proposal(binding, proposal))

    def __repr__(self):
        return '<InMemoryReferenceEnvelope: private unverified reference proposals>'

    def public_status(self):
        return {
            'schema': PUBLIC_SCHEMA,
            'question_set_sha256': self._sealed['question_set_sha256'],
            'question_count': len(self._sealed['items']),
            'status': 'UNVERIFIED_MODEL_PROPOSAL_ONLY',
            'execution_status': 'NOT_RUN',
            'technical_score': 'NOT_SCORED',
            'interviewer_reference_access': False,
            'questions': [
                {'question_sha256': q['question_sha256'], 'environment': q['environment'],
                 'reference_status': 'REFERENCE_UNVERIFIED_AI_PROPOSAL',
                 'alternative_count': len(q['approaches'])}
                for q in self._sealed['items']
            ],
        }

    def trusted_oracle_only(self, *, caller, interview_phase):
        # Not an authentication API: only trusted Native-side code may ever
        # hold the envelope. Runtime integration must enforce process authority.
        if caller != 'oracle' or interview_phase != 'PRIVATE_PREPARATION':
            raise PreparationContractError('PRIVATE_REFERENCE_ACCESS_DENIED')
        return copy.deepcopy(self._sealed)
