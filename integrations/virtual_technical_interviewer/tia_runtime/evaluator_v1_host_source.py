"""TIA E4D-02C1A trusted Host rehearsal -> 12D semantic source adapter.

No network, no database execution, no writes, no authority from candidate text.
Only a trusted Host may call with its internally loaded, frozen rehearsal AND
its append-only journal. A checksum is not authentication of a caller.

This additive slice does NOT register a Native/WebKit command. It generates
and validates model-ready *data*, never a paid request nor an approved grade.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from .evaluator_v1_semantic_contract import (
    SemanticContractError, compile_source, validate_source, strict_load,
    build_review_packet, PROPOSAL_SCHEMA,
)

CAP_BYTES = 2_000_000
MAX_EVENTS = 32
MAX_TEXT_BYTES = 65_536
STATUS_COMPLETE = 'COMPLETE'
SCHEMA = 'tia-e4d02c1a-host-source/v1'
CANONICAL_SCENARIOS = frozenset((
    'UNKNOWN', 'COMMON_PATH', 'VALID_ALTERNATIVE_UNVERIFIED',
    'ONE_SHOT_CODE', 'STUCK_DIAGNOSTIC',
))
CANDIDATE_KINDS = frozenset(('clarify', 'plan', 'implement', 'test', 'help'))

class HostSourceError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _fail(code):
    raise HostSourceError(code)


def _canonical(value):
    try:
        data = json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, OverflowError, RecursionError):
        _fail('INVALID_HOST_JSON')
    if len(data) > CAP_BYTES:
        _fail('HOST_RECORD_TOO_LARGE')
    return data


def _sha(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _utf8_excerpt(text, limit=600):
    """Retain valid Unicode prefix; exact cited bytes are represented by SHA."""
    if type(text) is not str or not text.strip():
        _fail('EMPTY_OR_INVALID_EVENT_TEXT')
    raw = text.encode('utf-8')
    if len(raw) > MAX_TEXT_BYTES:
        _fail('EVENT_TEXT_TOO_LARGE')
    return raw[:limit].decode('utf-8', errors='ignore')


def _snapshot(plan, journal):
    if (type(plan) is not dict or plan.get('status') != STATUS_COMPLETE or
            type(plan.get('questions')) is not list or len(plan['questions']) != 3 or
            type(plan.get('results')) is not list or len(plan['results']) != 3):
        _fail('REHEARSAL_NOT_FROZEN_COMPLETE')
    if type(journal) is not list or not journal:
        _fail('TRUSTED_JOURNAL_REQUIRED')
    # SHA binds the complete snapshot, not only excerpts; it is not a MAC/signature.
    bound = {'rehearsal': plan, 'journal': journal}
    return _sha(bound)


def compile_host_source(plan, journal, question_index, *, scenario='UNKNOWN'):
    """Compile frozen candidate events to the exact E4D02C0 contract.

    This should be called from Host internals after lock/recovery validation,
    never on direct renderer input or uploaded arbitrary JSON.
    """
    if type(question_index) is not int or question_index not in (0, 1, 2):
        _fail('INVALID_QUESTION_INDEX')
    if type(scenario) is not str or scenario not in CANONICAL_SCENARIOS:
        _fail('INVALID_INTERVIEW_SCENARIO')
    journal_sha = _snapshot(plan, journal)
    question = plan['questions'][question_index]
    result = plan['results'][question_index]
    if type(question) is not dict or type(result) is not dict:
        _fail('INVALID_QUESTION_OR_RESULT')
    # Match question slot and original source hash when native rehearsal has them.
    if ('index' in result and (type(result['index']) is not int or result['index'] != question_index)):
        _fail('CROSS_QUESTION_RESULT_INDEX')
    if ('question_sha256' in result and type(question.get('content_sha256')) is str
            and result['question_sha256'] != question['content_sha256']):
        _fail('CROSS_QUESTION_SOURCE_HASH')
    session = result.get('session')
    if session is None and result.get('outcome') in ('SKIPPED', 'NO_SUBMISSION'):
        raw_events = []
    elif type(session) is dict and type(session.get('events')) is list:
        raw_events = session['events']
    else:
        _fail('QUESTION_SESSION_NOT_FROZEN')
    events = []
    ids = set()
    for event in raw_events:
        if type(event) is not dict:
            _fail('INVALID_JOURNAL_EVENT')
        actor, kind, event_id = event.get('actor'), event.get('kind'), event.get('id')
        # Do not misclassify Host or provider metadata as candidate evidence.
        if actor == 'candidate':
            if kind not in CANDIDATE_KINDS:
                _fail('UNKNOWN_CANDIDATE_ACTION')
        elif actor == 'interviewer' and kind == 'reply' and event.get('provenance') == 'LIVE_MODEL':
            if type(event.get('payload')) is not dict or event['payload'].get('operation') != 'reply':
                _fail('INVALID_INTERVIEWER_REPLY')
        else:
            continue
        if type(event_id) is not str or event_id in ids:
            _fail('DUPLICATE_OR_INVALID_EVENT_ID')
        ids.add(event_id)
        payload = event.get('payload')
        if type(payload) is not dict:
            _fail('INVALID_EVENT_PAYLOAD')
        excerpt = _utf8_excerpt(payload.get('text'))
        events.append({'id': event_id, 'question_index': question_index,
                       'actor': actor, 'kind': kind, 'excerpt': excerpt,
                       'excerpt_sha256': hashlib.sha256(excerpt.encode('utf-8')).hexdigest()})
        if len(events) > MAX_EVENTS:
            _fail('EVIDENCE_TRUNCATION_NOT_ALLOWED')
    # Both SQL code and original question content remain in the private Host;
    # their complete representation is bound by the full snapshot digest.
    try:
        source = compile_source(_sha(question), question_index, events, scenario, journal_sha)
        validate_source(source)
    except SemanticContractError as error:
        _fail('SEMANTIC_SOURCE_REJECTED_' + error.code)
    return source


def verify_source_still_current(plan, journal, source):
    """Reject stale source on any journal, code, or question mutation."""
    if type(source) is not dict:
        _fail('INVALID_SEMANTIC_SOURCE')
    try:
        validate_source(source)
    except SemanticContractError:
        _fail('SEMANTIC_SOURCE_TAMPERED')
    fresh = compile_host_source(plan, journal, source['question_index'],
                                scenario=source['scenario'])
    if fresh != source:
        _fail('STALE_SEMANTIC_SOURCE')
    return True


def review_untrusted_proposal_json(plan, journal, source, raw_json):
    """Validate untrusted JSON and return *review packet*, never a score."""
    verify_source_still_current(plan, journal, source)
    try:
        proposal = strict_load(raw_json)
        result = build_review_packet(source, proposal)
    except SemanticContractError as error:
        _fail('UNTRUSTED_PROPOSAL_REJECTED_' + error.code)
    return result


def prepare_host_only_packet(plan, journal, question_index, scenario='UNKNOWN'):
    """Bounded protocol payload for future native adapter; NOT a callable spec."""
    source = compile_host_source(plan, journal, question_index, scenario=scenario)
    return {'schema': SCHEMA, 'role': 'evaluator',
            'source_sha256': source['source_sha256'],
            'proposal_schema': PROPOSAL_SCHEMA, 'source': source,
            'status': 'HOST_ONLY_NOT_NATIVE_AUTHORIZED',
            'paid_calls': 0, 'score': None, 'can_submit_provider_request': False}
