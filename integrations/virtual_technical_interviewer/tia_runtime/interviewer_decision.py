"""E4-C2A offline Host-owned adaptive interviewer decision policy.

Contract-only: not connected to app_host, the paid provider or the native vault.
No reference answers, hidden reasoning, automatic hint escalation, code execution,
score authority, or ability certification are emitted by this policy.
"""
from __future__ import annotations

import re
from typing import Mapping

from .trajectory_evidence import SCHEMA as OBS_SCHEMA, EvidenceContractError

DECISION_SCHEMA = 'tia-interviewer-policy-proposal/v0.1'
PHASES = {'INTERVIEWING', 'CLOSED'}
MECHANISMS = {'STRICT_CHALLENGING', 'PROFESSIONAL_SUPPORTIVE'}
HYPOTHESES = {'VALID_ALTERNATIVE', 'PROMISING_UNVERIFIED', 'LOCAL_BUG',
              'STRUCTURAL_GAP', 'NEEDS_CLARIFICATION', 'UNKNOWN'}
ACTIONS = {'CLARIFY', 'REQUEST_INVARIANT', 'REQUEST_TEST', 'REQUEST_COUNTEREXAMPLE',
           'REQUEST_EXPLANATION', 'DECLINE', 'DIAGNOSTIC_QUESTION', 'CLOSE'}
_ALLOWED_PROPOSAL_KEYS = {'schema', 'candidate_event_ids', 'observed_action', 'hypotheses',
                          'evidence_refs', 'execution_receipt_ref', 'uncertainty',
                          'authorized_action', 'max_hint_level', 'disclosure_scope',
                          'candidate_facing_reply'}
_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$')
_SHA = re.compile(r'^[0-9a-f]{64}$')


def decide_turn(*, observation: Mapping[str, object], phase: str,
                time_left_seconds: int, mechanism: str, hints_used: int = 0,
                completed_questions: int = 0,
                host_receipts: tuple[Mapping[str, object], ...] = ()) -> dict:
    """Select one action from trusted, read-only Host observation.

    This is a decision *summary*, not a prompt asking the model to deliberate.
    Alternatives are permitted hypotheses, not verdicts of global correctness.
    """
    if not isinstance(observation, Mapping) or set(observation) != {
        'schema', 'question_sha256', 'question_environment', 'candidate_event_ids',
        'observed_action', 'execution_receipt_ref', 'execution_status', 'candidate_text_stored'
    } or observation['schema'] != OBS_SCHEMA:
        raise EvidenceContractError('INVALID_OBSERVATION')
    refs = observation['candidate_event_ids']
    if (type(refs) is not list or len(refs) != 1 or type(refs[0]) is not str
        or not _ID.fullmatch(refs[0]) or type(observation['question_sha256']) is not str
        or not _SHA.fullmatch(observation['question_sha256'])
        or observation['question_environment'] not in ('POSTGRESQL', 'PANDAS')
        or observation['observed_action'] not in ('CLARIFY', 'PLAN', 'IMPLEMENT', 'TEST', 'HELP')
        or observation['candidate_text_stored'] is not False):
        raise EvidenceContractError('UNTRUSTED_OBSERVATION')
    receipt_ref = observation['execution_receipt_ref']
    if receipt_ref is not None and (type(receipt_ref) is not str or not _ID.fullmatch(receipt_ref)):
        raise EvidenceContractError('INVALID_RECEIPT_REF')
    status = observation['execution_status']
    if status not in ('PASSED', 'FAILED', 'ERROR', 'NOT_VERIFIED') or (receipt_ref is None and status != 'NOT_VERIFIED'):
        raise EvidenceContractError('UNTRUSTED_TEST_STATUS')
    # Defense in depth: even a forged stand-alone observation cannot turn a
    # renderer/model claim into a verified local fixture result. Only the
    # Host-owned receipt registry may authorize that status.
    if type(host_receipts) is not tuple:
        raise EvidenceContractError('INVALID_HOST_RECEIPT_REGISTRY')
    if receipt_ref is not None:
        matches = [r for r in host_receipts if isinstance(r, Mapping) and r.get('receipt_id') == receipt_ref]
        if len(matches) != 1 or set(matches[0]) != {'receipt_id', 'question_sha256', 'candidate_event_id', 'result'}:
            raise EvidenceContractError('RECEIPT_NOT_HOST_OWNED')
        verified = matches[0]
        if (verified['question_sha256'] != observation['question_sha256']
            or verified['candidate_event_id'] != refs[0] or verified['result'] != status):
            raise EvidenceContractError('RECEIPT_REVALIDATION_FAILED')
    if type(phase) is not str or type(mechanism) is not str or phase not in PHASES or mechanism not in MECHANISMS:
        raise EvidenceContractError('UNAPPROVED_PHASE_OR_MECHANISM')
    if any(type(x) is not int or x < 0 for x in (time_left_seconds, hints_used, completed_questions)):
        raise EvidenceContractError('INVALID_HOST_CLOCK_OR_COUNTS')
    if hints_used != 0:
        # H1-H3 is an unapproved future policy; do not silently reinterpret it.
        raise EvidenceContractError('HINT_POLICY_NOT_AUTHORIZED')
    action = observation['observed_action']
    if phase == 'CLOSED' or time_left_seconds == 0:
        choice, hypotheses, uncertainty = 'CLOSE', ['UNKNOWN'], 'Session closed by Host'
    elif action == 'HELP':
        choice = 'DECLINE' if mechanism == 'STRICT_CHALLENGING' else 'DIAGNOSTIC_QUESTION'
        hypotheses, uncertainty = ['UNKNOWN'], 'Request for assistance is not evidence of inability'
    elif action == 'CLARIFY':
        choice, hypotheses, uncertainty = 'CLARIFY', ['NEEDS_CLARIFICATION', 'UNKNOWN'], 'Question may be ambiguous'
    elif status == 'PASSED':
        choice = 'REQUEST_EXPLANATION'
        hypotheses = ['VALID_ALTERNATIVE', 'PROMISING_UNVERIFIED']
        uncertainty = 'Only the specifically approved local fixture passed; global correctness unproven'
    elif status in ('FAILED', 'ERROR'):
        choice = 'REQUEST_COUNTEREXAMPLE'
        hypotheses = ['LOCAL_BUG', 'UNKNOWN']
        uncertainty = 'Local execution evidence does not establish root cause or ability'
    elif action == 'PLAN':
        choice, hypotheses, uncertainty = 'REQUEST_INVARIANT', ['PROMISING_UNVERIFIED', 'UNKNOWN'], 'Plan not independently verified'
    elif action in ('IMPLEMENT', 'TEST'):
        choice, hypotheses, uncertainty = 'REQUEST_TEST', ['PROMISING_UNVERIFIED', 'UNKNOWN'], 'No independently verified local fixture'
    else:
        choice, hypotheses, uncertainty = 'DIAGNOSTIC_QUESTION', ['UNKNOWN'], 'Insufficient evidence'
    assert choice in ACTIONS and set(hypotheses).issubset(HYPOTHESES)
    return {'schema': DECISION_SCHEMA, 'candidate_event_ids': refs.copy(),
            'observed_action': action, 'hypotheses': hypotheses,
            'evidence_refs': refs.copy(), 'execution_receipt_ref': receipt_ref,
            'uncertainty': uncertainty, 'authorized_action': choice,
            'max_hint_level': 'H0', 'disclosure_scope': 'PUBLIC_TASK_ONLY'}


def public_interviewer_packet(*, decision: Mapping[str, object],
                              public_question: Mapping[str, object], expected_question_sha256: str) -> dict:
    """Compile *allowlisted* public inputs. No private reference/vault argument exists.

    A caller cannot pass reference solutions, grades, executable model tools,
    an override of the action gate, or a policy/hint escalation.
    """
    allowed = {'question_id', 'question_sha256', 'environment', 'statement', 'schema',
               'constraints', 'examples'}
    if not isinstance(public_question, Mapping) or not set(public_question).issubset(allowed):
        raise EvidenceContractError('PRIVATE_OR_UNKNOWN_QUESTION_FIELD')
    required = {'question_id', 'question_sha256', 'environment', 'statement'}
    if not required.issubset(public_question) or any(
        type(public_question[k]) is not str or not public_question[k].strip()
        for k in required
    ):
        raise EvidenceContractError('INVALID_PUBLIC_QUESTION')
    if type(expected_question_sha256) is not str or not _SHA.fullmatch(expected_question_sha256) or public_question['question_sha256'] != expected_question_sha256:
        raise EvidenceContractError('QUESTION_MISMATCH')
    for key, value in public_question.items():
        if key not in required and type(value) not in (str, list):
            raise EvidenceContractError('INVALID_PUBLIC_FIELD')
        if isinstance(value, str) and len(value.encode('utf-8')) > 8192:
            raise EvidenceContractError('OVERSIZED_PUBLIC_INPUT')
        if isinstance(value, list) and (len(value) > 5 or any(type(s) is not str or len(s.encode('utf-8')) > 2048 for s in value)):
            raise EvidenceContractError('OVERSIZED_PUBLIC_INPUT')
    if (not isinstance(decision, Mapping) or set(decision) != _ALLOWED_PROPOSAL_KEYS - {'candidate_facing_reply'}
        or decision['schema'] != DECISION_SCHEMA or decision['disclosure_scope'] != 'PUBLIC_TASK_ONLY'
        or decision['max_hint_level'] != 'H0'):
        raise EvidenceContractError('UNTRUSTED_POLICY_DECISION')
    return {'schema': 'tia-interviewer-context/v1',
            'question': {key: list(value) if type(value) is list else value for key, value in public_question.items()},
            'decision': {key: list(value) if type(value) is list else value for key, value in decision.items()}}


def validate_model_reply(*, decision: Mapping[str, object], proposal: Mapping[str, object]) -> dict:
    """Reject model attempts to increase rights, invent grades, or alter receipt refs.

    Text itself is untrusted and may still require semantic safety screening at
    the later Host integration; this module cannot certify that a generated
    answer is nonleaking merely by checking its shape.
    """
    if not isinstance(decision, Mapping) or not isinstance(proposal, Mapping):
        raise EvidenceContractError('INVALID_MODEL_PROPOSAL')
    if set(decision) != _ALLOWED_PROPOSAL_KEYS - {'candidate_facing_reply'} or set(proposal) != _ALLOWED_PROPOSAL_KEYS:
        raise EvidenceContractError('MODEL_PROPOSAL_AUTHORITY_FIELDS')
    if any(proposal[key] != value for key, value in decision.items()):
        raise EvidenceContractError('MODEL_OVERRIDES_HOST_DECISION')
    reply = proposal['candidate_facing_reply']
    if type(reply) is not str or not reply.strip() or len(reply.encode('utf-8')) > 600 or any(
        ord(ch) < 32 and ch not in '\n\t' for ch in reply
    ):
        raise EvidenceContractError('INVALID_CANDIDATE_REPLY')
    if '```' in reply:
        raise EvidenceContractError('UNAUTHORIZED_CODE_BLOCK')
    # Returned projection never has secret code, grades or Host mutations.
    return {'schema': DECISION_SCHEMA, **{k: (list(v) if type(v) is list else v) for k, v in decision.items()},
            'candidate_facing_reply': reply}
