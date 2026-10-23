"""E4-C0: Host-owned *read-only* private-preparation readiness projection.

No model calls, answer generation, reference-code handling, code execution,
provider selection, scoring, or modifications to persisted interview evidence.
The public projection intentionally NEVER includes problem text, examples,
candidate code, reference answers, or an authority to produce a hint.
"""
from __future__ import annotations

import copy
import re
from .setup import SetupError, review_question

SCHEMA = 'tia-preflight-readiness/v1'
SHA = re.compile(r'[0-9a-f]{64}\Z')
ENVIRONMENTS = frozenset(('POSTGRESQL', 'PANDAS'))
MAX_QUESTIONS = 4


def _question_status(review, expected_environment, index):
    result = {
        'question_index': index,
        'status': 'REVIEW_REQUIRED',
        'question_sha256': None,
        'environment': 'UNKNOWN',
        'reference_status': 'NOT_GENERATED',
        'execution_status': 'NOT_RUN',
        'content_exposed': False,
    }
    if type(review) is not dict or type(review.get('fields')) is not dict:
        return result
    fields = review['fields']
    env = fields.get('environment')
    result['environment'] = env if env in ENVIRONMENTS else 'UNKNOWN'
    sha = review.get('content_sha256')
    if type(sha) is str and SHA.fullmatch(sha):
        result['question_sha256'] = sha
    if (type(env) is not str or env != expected_environment
            or review.get('human_confirmed') is not True
            or review.get('practice_eligible') is not True
            or type(sha) is not str or SHA.fullmatch(sha) is None):
        return result
    try:
        independently_reviewed = review_question(fields, expected_environment)
    except (SetupError, ValueError, TypeError, UnicodeError):
        return result
    if (independently_reviewed['issues'] or
            independently_reviewed['content_sha256'] != sha or
            independently_reviewed['structure_status'] != 'STRUCTURALLY_COMPLETE'):
        return result
    result['status'] = 'SOURCE_BOUND_CONFIRMED'
    return result


def build_preflight_readiness(config, reviews):
    """Pure additive Host projection; approved *inputs* are not solved outputs.

    It must be safe to call on every Host snapshot, including replay of old
    journals. Neither model output nor reference code is ever accepted here.
    """
    result = {
        'schema': SCHEMA, 'stage': 'C0_READ_ONLY_SHELL',
        'status': 'CONFIG_REQUIRED', 'required_count': None,
        'confirmed_count': 0, 'questions': [],
        'native_preparer_available': False, 'paid_requests_by_preflight': 0,
        'reference_solutions_generated': 0, 'code_executions_by_preflight': 0,
        'official_hidden_tests': False, 'technical_score': 'NOT_SCORED',
        'interviewer_reference_access': False,
        'live_four_question_supported': False,
    }
    if config is None:
        return result
    count = getattr(config, 'question_count', None)
    env = getattr(config, 'technical_environment', None)
    source = getattr(config, 'question_source', None)
    duration = getattr(config, 'duration_minutes', None)
    if (type(count) is not int or count not in (3, 4)
            or duration != (45 if count == 3 else 60)
            or env not in ENVIRONMENTS or source != 'BYOQ'
            or type(reviews) is not list or len(reviews) > MAX_QUESTIONS):
        result['status'] = 'UNSUPPORTED_OR_INVALID_CONFIGURATION'
        return result
    result['required_count'] = count
    result['questions'] = [_question_status(review, env, index)
                           for index, review in enumerate(reviews)]
    hashes = [q['question_sha256'] for q in result['questions']]
    duplicate = len(set(x for x in hashes if x is not None)) != len([x for x in hashes if x is not None])
    all_confirmed = (len(reviews) == count and not duplicate and
                     all(q['status'] == 'SOURCE_BOUND_CONFIRMED' for q in result['questions']))
    result['confirmed_count'] = sum(q['status'] == 'SOURCE_BOUND_CONFIRMED'
                                    for q in result['questions'])
    result['status'] = ('READY_FOR_FUTURE_PRIVATE_PREPARATION' if all_confirmed
                        else 'QUESTION_REVIEW_REQUIRED')
    # Existing live Host create_plan supports exactly three questions; never
    # claim 4-question rehearsals or paid pre-solve are functional in C0.
    result['live_four_question_supported'] = False
    return result


def public_role_view(preflight, role):
    """Only allowlisted metadata flows to renderer/interviewer/Trainer.

    A forged extra `reference_solution` key is not copied. This is a data
    minimization boundary, NOT a replacement for OS isolation of future vaults.
    """
    if role not in ('renderer', 'interviewer', 'trainer'):
        raise ValueError('UNKNOWN_PUBLIC_ROLE')
    if type(preflight) is not dict or preflight.get('schema') != SCHEMA:
        raise ValueError('INVALID_PREFLIGHT')
    public_fields = ('schema', 'stage', 'status', 'required_count', 'confirmed_count',
                     'native_preparer_available', 'paid_requests_by_preflight',
                     'reference_solutions_generated', 'code_executions_by_preflight',
                     'official_hidden_tests', 'technical_score',
                     'interviewer_reference_access', 'live_four_question_supported')
    qs = preflight.get('questions')
    if type(qs) is not list or len(qs) > MAX_QUESTIONS:
        raise ValueError('INVALID_PREFLIGHT')
    question_fields = ('question_index', 'status', 'question_sha256', 'environment',
                       'reference_status', 'execution_status', 'content_exposed')
    return {**{field: copy.deepcopy(preflight[field]) for field in public_fields},
            'questions': [{field: copy.deepcopy(q[field]) for field in question_fields}
                          for q in qs]}


def authorize_private_reference(role, phase, human_approved, *, capability_ready=False):
    """C0 fails closed; real oracle capability must be engineered in C1.

    This intentionally cannot issue an access token, even to a claimed Oracle.
    """
    if role not in ('preparer', 'oracle', 'interviewer', 'evaluator', 'trainer'):
        raise ValueError('UNKNOWN_ROLE')
    return {'granted': False, 'reason': 'C0_PRIVATE_REFERENCE_CAPABILITY_NOT_IMPLEMENTED',
            'code_execution_authorized': False, 'network_authorized': False}
