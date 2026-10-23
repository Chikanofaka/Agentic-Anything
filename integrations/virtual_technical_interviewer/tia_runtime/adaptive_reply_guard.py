"""C2B2A: narrow Host-side denial rules for untrusted interviewer model text.

This is NOT a semantic correctness proof or a substitute for a local executor.
It refuses explicit prohibited claims/answer-shaped code after the native model
responds, before any interviewer event is committed to the saved journal.
"""
from __future__ import annotations

import re
from typing import Mapping

GUARD_VERSION = 'E4C2B2A'
GUARD_POLICY = 'E4C2B1_HOST_DECISION'
_ACTIONS = frozenset({'CLARIFY', 'REQUEST_INVARIANT', 'REQUEST_TEST',
                     'REQUEST_COUNTEREXAMPLE', 'REQUEST_EXPLANATION',
                     'DECLINE', 'DIAGNOSTIC_QUESTION'})
_SHA = re.compile(r'^[a-f0-9]{64}$')
_LOCAL_REF = re.compile(r'^localpg-[a-f0-9]{64}$')
_BAD = (
    re.compile(r'```'),
    re.compile(r'(?im)^\s*(?:SELECT|WITH|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+\S'),
    re.compile(r'(?i)\b(?:your|the|this)\s+(?:sql|query|solution|code)\s+(?:has\s+)?passed\s+(?:all\s+)?tests\b'),
    re.compile(r'(?i)\b(?:i|we)\s+(?:have\s+)?(?:executed|ran|tested)\s+(?:your|the|this)\s+(?:sql|query|code)\b'),
    re.compile(r'(?i)\b(?:you|your\s+(?:code|solution))\s+(?:scored|earned|got)\s+\d+(?:\.\d+)?\s*(?:%|points?\b|/\d+)'),
    re.compile(r'(?i)\b(?:here\s+is|the\s+answer\s+is)\s+(?:the\s+)?(?:solution|correct\s+sql|query)\s*:'),
    re.compile(r'(?i)\b(?:use|try|write|apply)\s+(?:the\s+)?(?:row_number|dense_rank|rank)\s*\('),
    re.compile(r'(?i)(?:你的|您的)?(?:SQL|查询|代码|解法).{0,8}(?:通过了?所有测试|全部通过|已验证正确)'),
    re.compile(r'(?:你|您)?(?:得分|获得)\s*\d+(?:\.\d+)?\s*(?:分|%)'),
    re.compile(r'(?:正确答案|标准答案)\s*(?:是|为|：|:)'),
    re.compile(r'(?i)(?:使用|直接用|尝试)\s*(?:row_number|dense_rank|rank)\s*\('),
    re.compile(r'(?i)\"(?:score|grade|technical_score|communication_score|passed)\"\s*:'),
)

class ReplyGuardError(ValueError):
    code = 'ADAPTIVE_REPLY_NOT_AUTHORIZED'


def guard_adaptive_reply(policy: Mapping[str, object], reply: object) -> None:
    """Fail closed on forged Host authority or high-confidence forbidden claims.

    The native envelope remains {reply: text}. The Host, not WebKit, supplies
    the pending native transaction policy. Does not see Native reference data.
    """
    if (not isinstance(policy, Mapping)
            or policy.get('rule_id') != GUARD_POLICY
            or type(policy.get('action')) is not str
            or policy['action'] not in _ACTIONS
            or policy.get('max_hint_level') != 'H0'
            or policy.get('disclosure_scope') != 'PUBLIC_TASK_ONLY'
            or policy.get('technical') != 'NOT_SCORED'
            or not (
                (policy.get('receipt_status') == 'NOT_VERIFIED' and policy.get('execution_receipt_ref') is None)
                or (policy.get('receipt_status') in ('LOCAL_FIXTURE_PASSED', 'LOCAL_FIXTURE_FAILED',
                                                     'LOCAL_FIXTURE_ERROR')
                    and type(policy.get('execution_receipt_ref')) is str
                    and _LOCAL_REF.fullmatch(policy['execution_receipt_ref']))
            )
            or type(policy.get('question_sha256')) is not str
            or _SHA.fullmatch(policy['question_sha256']) is None
            or type(policy.get('candidate_event_ids')) is not list
            or len(policy['candidate_event_ids']) != 1):
        raise ReplyGuardError('HOST_POLICY_NOT_AUTHORIZED')
    if type(reply) is not str or not reply.strip():
        raise ReplyGuardError('EMPTY_MODEL_REPLY')
    try:
        if len(reply.encode('utf-8')) > 8000 or len(reply) > 2000:
            raise ReplyGuardError('OVERSIZED_MODEL_REPLY')
    except UnicodeError:
        raise ReplyGuardError('INVALID_MODEL_REPLY') from None
    if any(ord(char) < 32 and char not in '\n\t' for char in reply):
        raise ReplyGuardError('CONTROL_IN_MODEL_REPLY')
    if any(pattern.search(reply) for pattern in _BAD):
        raise ReplyGuardError('MODEL_REPLY_FORBIDDEN_CLAIM')
