"""TIA E4D-02C0: offline, event-bound, reviewer-gated semantic proposal contract.

No provider calls, code execution, final scores, employment predictions or writes.
This validates a model's *proposal*, NOT whether the model's interpretation is true.
It deliberately does not modify the 02A host-owned scoring kernel or 02B Mock UI.
Only the trusted Host may compile the source packet from its frozen journal.
"""
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy

SOURCE_SCHEMA = 'tia-e4d02c0-semantic-source/v1'
PROPOSAL_SCHEMA = 'tia-e4d02c0-semantic-proposal/v1'
REVIEW_SCHEMA = 'tia-e4d02c0-review-packet/v1'
DIMENSIONS = tuple(f'{axis}{n}' for axis in 'TCP' for n in range(1, 5))
SCENARIOS = frozenset(('COMMON_PATH', 'VALID_ALTERNATIVE_UNVERIFIED', 'ONE_SHOT_CODE',
                       'STUCK_DIAGNOSTIC', 'UNKNOWN'))
KINDS = frozenset(('clarify', 'plan', 'implement', 'sql_submission', 'test',
                   'test_idea', 'help', 'help_request', 'closing'))
ID_PATTERN = re.compile(r'[A-Za-z0-9_.:-]{1,160}\Z')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')
MODEL_ROLES = frozenset(('evaluator',))
SEVERITY = frozenset(('LOW', 'MEDIUM'))


class SemanticContractError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _reject(code):
    raise SemanticContractError(code)


def strict_load(text):
    if type(text) is not str or len(text.encode('utf-8')) > 65536:
        _reject('INVALID_JSON_SIZE')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                _reject('DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def invalid_constant(value):
        _reject('NONFINITE_JSON_VALUE')
    try:
        return json.loads(text, object_pairs_hook=unique, parse_constant=invalid_constant)
    except SemanticContractError:
        raise
    except (ValueError, TypeError, RecursionError):
        _reject('INVALID_JSON')


def _canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def _digest(data):
    return hashlib.sha256(_canonical(data).encode('utf-8')).hexdigest()


def _exact(value, fields, error):
    if type(value) is not dict or set(value) != set(fields):
        _reject(error)


def compile_source(question_sha256, question_index, events, scenario,
                   journal_digest, frozen=True):
    """Compile bounded candidate evidence; caller must be trusted Host.

    A SHA proves a byte match, *not* that the caller truly owns a valid journal.
    Never use this API on arbitrary renderer-supplied events.
    """
    if (type(frozen) is not bool or not frozen or type(question_sha256) is not str
            or not HEX64.fullmatch(question_sha256) or type(journal_digest) is not str
            or not HEX64.fullmatch(journal_digest) or type(question_index) is not int
            or not 0 <= question_index <= 3 or type(scenario) is not str
            or scenario not in SCENARIOS):
        _reject('SOURCE_NOT_FROZEN_OR_BOUND')
    if type(events) is not list or len(events) > 32:
        _reject('INVALID_SOURCE_EVENTS')
    normalized, seen = [], set()
    for record in events:
        _exact(record, ('id', 'question_index', 'actor', 'kind', 'excerpt', 'excerpt_sha256'),
               'INVALID_SOURCE_EVENT_SHAPE')
        identifier, excerpt = record['id'], record['excerpt']
        if (type(identifier) is not str or not ID_PATTERN.fullmatch(identifier)
                or identifier in seen or type(record['question_index']) is not int
                or record['question_index'] != question_index
                or record['actor'] not in ('candidate', 'interviewer')
                or type(record['kind']) is not str
                or (record['actor'] == 'candidate' and record['kind'] not in KINDS)
                or (record['actor'] == 'interviewer' and record['kind'] != 'reply')
                or type(excerpt) is not str or not excerpt.strip()
                or len(excerpt.encode('utf-8')) > 600
                or type(record['excerpt_sha256']) is not str
                or record['excerpt_sha256'] != hashlib.sha256(excerpt.encode('utf-8')).hexdigest()):
            _reject('INVALID_OR_CROSS_QUESTION_EVENT')
        seen.add(identifier)
        normalized.append(deepcopy(record))
    content = dict(schema=SOURCE_SCHEMA, question_sha256=question_sha256,
                   question_index=question_index, journal_digest=journal_digest,
                   scenario=scenario, evidence=normalized,
                   input_limit='BOUNDED_EXCERPTS_NOT_COMPLETE_SOURCE',
                   execution_truth='NO_EXECUTION_CLAIM_IN_THIS_CONTRACT',
                   rubric='E4D-12-DIMENSIONS-MVM-UNCALIBRATED')
    content['source_sha256'] = _digest(content)
    return content


def validate_source(source):
    _exact(source, ('schema', 'question_sha256', 'question_index', 'journal_digest',
                    'scenario', 'evidence', 'input_limit', 'execution_truth',
                    'rubric', 'source_sha256'), 'INVALID_SOURCE_SHAPE')
    if source['schema'] != SOURCE_SCHEMA or type(source['source_sha256']) is not str:
        _reject('INVALID_SOURCE_SCHEMA')
    copied = dict(source)
    checksum = copied.pop('source_sha256')
    if checksum != _digest(copied):
        _reject('SOURCE_DIGEST_MISMATCH')
    expected = compile_source(source['question_sha256'], source['question_index'],
                              source['evidence'], source['scenario'],
                              source['journal_digest'])
    if expected != source:
        _reject('INVALID_SOURCE_CANONICALIZATION')
    return True


def validate_proposal(source, proposal):
    validate_source(source)
    _exact(proposal, ('schema', 'role', 'source_sha256', 'dimensions', 'summary'),
           'INVALID_PROPOSAL_SHAPE')
    if (proposal['schema'] != PROPOSAL_SCHEMA or type(proposal['role']) is not str or proposal['role'] not in MODEL_ROLES
            or type(proposal['source_sha256']) is not str
            or proposal['source_sha256'] != source['source_sha256']):
        _reject('STALE_OR_UNAUTHORIZED_PROPOSAL')
    if type(proposal['dimensions']) is not list or len(proposal['dimensions']) != 12:
        _reject('INCOMPLETE_12_DIMENSION_PROPOSAL')
    candidate_events = {e['id']: e for e in source['evidence'] if e['actor'] == 'candidate'}
    seen = set()
    for item in proposal['dimensions']:
        _exact(item, ('id', 'anchor', 'evidence_ids', 'reason', 'confidence'),
               'INVALID_DIMENSION_SHAPE')
        name, anchor, ids, reason = (item['id'], item['anchor'],
                                     item['evidence_ids'], item['reason'])
        if type(name) is not str or name not in DIMENSIONS or name in seen:
            _reject('INVALID_DIMENSION_ID')
        seen.add(name)
        if anchor is not None and (type(anchor) is not int or not 0 <= anchor <= 4):
            _reject('INVALID_ANCHOR')
        if type(ids) is not list or len(ids) > 5 or any(type(i) is not str for i in ids) or len(set(ids)) != len(ids):
            _reject('INVALID_EVIDENCE_IDS')
        if any(i not in candidate_events for i in ids):
            _reject('CROSS_QUESTION_OR_NONCANDIDATE_CITATION')
        if (type(reason) is not str or len(reason.strip()) < 5 or len(reason.encode('utf-8')) > 500
                or type(item['confidence']) is not str):
            _reject('INVALID_REASON_OR_CONFIDENCE')
        if anchor is None:
            if ids or item['confidence'] != 'NOT_ASSESSED':
                _reject('MISSING_EVIDENCE_NOT_ZERO')
        elif not ids or item['confidence'] not in SEVERITY:
            _reject('UNCITED_OR_UNCALIBRATED_ANCHOR')
    if seen != set(DIMENSIONS):
        _reject('DIMENSION_SET_MISMATCH')
    summary = proposal['summary']
    if type(summary) is not str or not 5 <= len(summary.strip()) <= 800:
        _reject('INVALID_SUMMARY')
    # No model-supplied score, percentiles, pass/fail, authority, eligibility, or hiring decision.
    # The schema's exact field allowlists enforce this structurally.
    return True


def build_review_packet(source, proposal):
    """Emit evidence-linked proposals, not a scored or verified outcome."""
    validate_proposal(source, proposal)
    candidate = {e['id']: e for e in source['evidence'] if e['actor'] == 'candidate'}
    lines = []
    for dim in proposal['dimensions']:
        lines.append({'id': dim['id'], 'proposed_anchor': dim['anchor'],
                      'status': 'NOT_OBSERVED' if dim['anchor'] is None else 'REVIEW_REQUIRED',
                      'evidence': [{'event_id': i,
                                    'excerpt_sha256': candidate[i]['excerpt_sha256']}
                                   for i in dim['evidence_ids']],
                      'reason': dim['reason'], 'confidence': dim['confidence']})
    output = {'schema': REVIEW_SCHEMA, 'status': 'HUMAN_REVIEW_REQUIRED',
              'authority': 'MODEL_PROPOSAL_ONLY',
              'question_index': source['question_index'],
              'question_sha256': source['question_sha256'],
              'journal_digest': source['journal_digest'],
              'scenario': source['scenario'],
              'source_sha256': source['source_sha256'],
              'dimensions': lines,
              'eligible_for_host_scoring': False,
              'scoring_kernel_handoff': 'BLOCKED_UNTIL_REVIEW_AND_REAL_KERNEL_ADAPTER',
              'verified_code_execution': False,
              'overall_score': None,
              'industry_percentile': None,
              'limitations': ['Proposal citations establish provenance, not semantic correctness.',
                              'No SQL/Pandas execution or local fixture is certified here.',
                              'No uncalibrated anchor is a hiring or competence decision.']}
    output['review_sha256'] = _digest(output)
    return output
