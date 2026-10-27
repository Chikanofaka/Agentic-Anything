"""E4-C2B1 adapter: Host-owned candidate event -> deterministic permitted action.

Input strictly originates in the Python Host journal, never the WebKit renderer.
This module cannot access the Native Preparer vault or assert global correctness.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Mapping

from .trajectory_evidence import EvidenceContractError, project_observation
from .interviewer_decision import decide_turn
from .local_fixture_evidence import bind_local_sql_fixture

POLICY_VERSION = 'E4C2B1'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
EVIDENCE_POLICY_VERSION = 'E4C2B2B'
_EVENT_KIND = {'clarify': 'CLARIFY', 'plan': 'PLAN', 'implement': 'IMPLEMENT',
               'test': 'TEST', 'help': 'HELP'}
_SHA = re.compile(r'[0-9a-f]{64}\Z')


def host_turn_policy(*, event: Mapping[str, object], public_question: Mapping[str, object],
                     host_candidate_ids: tuple[str, ...], mechanism: str,
                     phase: str, time_left_seconds: int,
                     implementation: Mapping[str, object] | None = None,
                     approved_local_grade: Mapping[str, object] | None = None,
                     question_index: int | None = None) -> dict:
    """Produce the ONLY Host action authorization for a new reply turn.

    B2 independent verification is not connected; executions are all unverified
    in this adapter. Candidate saying 'passed' cannot change that status.
    """
    if (not isinstance(event, Mapping) or set(event) != {'id', 'kind', 'payload'}
        or not isinstance(event['payload'], Mapping)
        or set(event['payload']) != {'text'}):
        raise EvidenceContractError('HOST_EVENT_SHAPE')
    kind = event['kind']
    if type(kind) is not str or kind not in _EVENT_KIND:
        raise EvidenceContractError('HOST_EVENT_ACTION')
    if not isinstance(public_question, Mapping):
        raise EvidenceContractError('HOST_QUESTION_SHAPE')
    qenv = public_question.get('environment')
    qsha = public_question.get('content_sha256')
    if type(qsha) is not str or not _SHA.fullmatch(qsha):
        # An original S03-C tutorial-preview question has no content_sha256.
        # Use a stable Host-calculated digest, not a candidate-supplied label.
        public_binding = {k: public_question.get(k) for k in ('id', 'statement', 'schema', 'environment')}
        if any(type(v) is not str or not v for v in public_binding.values()):
            raise EvidenceContractError('HOST_QUESTION_BINDING')
        qsha = hashlib.sha256(json.dumps(public_binding, sort_keys=True, separators=(',', ':'),
                                         ensure_ascii=True).encode()).hexdigest()
    obs = project_observation(event={'event_id': event['id'], 'kind': _EVENT_KIND[kind],
                                     'text': event['payload']['text']},
                              known_event_ids=host_candidate_ids,
                              question_sha256=qsha, question_environment=qenv)
    local = None
    if any(x is not None for x in (implementation, approved_local_grade, question_index)):
        if (kind != 'test' or qenv != 'POSTGRESQL'
                or implementation is None or approved_local_grade is None
                or question_index is None):
            raise EvidenceContractError('LOCAL_FIXTURE_UNAUTHORIZED_CONTEXT')
        local = bind_local_sql_fixture(question_sha256=qsha,
            question_index=question_index, implementation=implementation,
            candidate_ids=host_candidate_ids, grade=approved_local_grade)
        # C2A's verifier binds receipts to the *implementation*, not this new
        # TEST event. Never forge an event ID to imply this test itself passed.
        verified_obs = project_observation(
            event={'event_id': implementation['id'], 'kind': 'IMPLEMENT',
                   'text': implementation['payload']['text']},
            known_event_ids=host_candidate_ids, question_sha256=qsha,
            question_environment=qenv, receipt_ref=local['receipt_id'],
            host_receipts=(local,))
        policy = decide_turn(observation=verified_obs, phase=phase,
            time_left_seconds=time_left_seconds, mechanism=mechanism,
            host_receipts=(local,))
    else:
        policy = decide_turn(observation=obs, phase=phase,
                             time_left_seconds=time_left_seconds, mechanism=mechanism)
    # Never transmit code, fixture rows, private solutions, or overall grades.
    return {'rule_id': POLICY_VERSION + '_HOST_DECISION',
            'action': policy['authorized_action'],
            'candidate_event_ids': [event['id']],
            'question_sha256': qsha,
            'hypotheses': list(policy['hypotheses']),
            'uncertainty': policy['uncertainty'],
            'receipt_status': ('LOCAL_FIXTURE_' + local['result'] if local else 'NOT_VERIFIED'),
            'execution_receipt_ref': (local['receipt_id'] if local else None),
            'max_hint_level': 'H0',
            'disclosure_scope': 'PUBLIC_TASK_ONLY',
            'technical': 'NOT_SCORED', 'communication': 'OBSERVATION_ONLY'}


def seconds_remaining(rehearsal: object) -> int:
    """Only Host-owned/replayed timing may restrict a 45m interview.

    The special preview outside rehearsal has its own controller deadline;
    this is a policy upper bound, not a new source of time authority.
    """
    if rehearsal is None:
        return 86400
    if not isinstance(rehearsal, dict):
        raise EvidenceContractError('INVALID_REHEARSAL_CLOCK')
    timing = rehearsal.get('timing')
    if timing is None:
        return 2700
    if type(timing) is not dict or type(timing.get('limit_seconds')) is not int:
        raise EvidenceContractError('INVALID_REHEARSAL_CLOCK')
    elapsed = timing.get('elapsed_seconds')
    limit = timing['limit_seconds']
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0 or limit != 2700:
        raise EvidenceContractError('INVALID_REHEARSAL_CLOCK')
    if rehearsal.get('continuity_policy') == 'tia-continuity/v3':
        questions = timing.get('questions')
        index = timing.get('current_question')
        if (timing.get('question_limit_seconds') != 900 or type(questions) is not list
                or type(index) is not int or index not in range(len(questions))):
            raise EvidenceContractError('INVALID_REHEARSAL_CLOCK')
        current = questions[index].get('elapsed_seconds')
        if type(current) not in (int, float) or not math.isfinite(current) or current < 0:
            raise EvidenceContractError('INVALID_REHEARSAL_CLOCK')
        return max(0, 900 - math.ceil(current))
    return max(0, limit - math.ceil(elapsed))
