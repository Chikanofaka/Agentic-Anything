"""Versioned practice-only zero for a complete, code-only submitted record.

This is an observation about recorded demonstration, never a claim about ability
or a rewrite of a saved model proposal. Missing/broken records remain unknown.
"""
import hashlib
import json
import re
from .code_only_sql import has_recognized_select_syntax

POLICY = 'tia-recorded-communication/v1'
WEIGHTS = {'C01': 6, 'C02': 7, 'C03': 7, 'C04': 9, 'C05': 7, 'C06': 4}


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _bare_help(text):
    return bool(re.fullmatch(r'\s*(?:please\s+)?(?:help(?:\s+me)?|give\s+me\s+(?:a\s+)?hint|'
                            r'can\s+you\s+help(?:\s+me)?|(?:请)?帮(?:帮)?我|(?:请)?给我(?:一个)?提示)'
                            r'(?:,?\s+please)?[?!.。？！\s]*',
                            text, re.I))


def _only_code(text):
    # Conservative: comments or prose outside a fence could explain the work.
    value = text.strip()
    if value.startswith('```'):
        match = re.fullmatch(r'```(?:sql|SQL)?\s*\n(.*?)\n```', value, re.S)
        if not match:
            return False
        value = match[1].strip()
    if '--' in value or '/*' in value:
        return False
    if not re.match(r'^(?:SELECT|WITH)\b', value, re.I):
        return False
    # Any explicit explanation preserves semantic review, even on implement.
    if re.search(r'\b(?:my plan|because|i (?:will|used|chose|think)|we (?:will|need))\b|因为|我的计划|我(?:将|会|选择)', value, re.I):
        return False
    # A SELECT/WITH prefix is also ordinary explanatory language. Require the
    # whole text to match supported SQL structure; ambiguity keeps review open.
    return has_recognized_select_syntax(value)


def recorded_communication(plan, index):
    out = {'policy': POLICY, 'status': 'RECORD_UNAVAILABLE', 'points': None,
           'maximum_points': 40, 'dimensions': [], 'source_event_ids': [],
           'record_sha256': None, 'formal_grade': 'NOT_SCORED',
           'recording_health': 'NOT_ATTESTED',
           'meaning': 'Recorded demonstration only; no inference of communication ability.'}
    if plan.get('continuity_policy') != 'tia-continuity/v3':
        return dict(out, status='LEGACY_POLICY_UNCHANGED')
    results = plan.get('results')
    if (plan.get('status') != 'COMPLETE' or type(results) is not list or
            type(index) is not int or not 0 <= index < len(results)):
        return out
    result = results[index]
    session = result.get('session') if type(result) is dict else None
    events = session.get('events') if type(session) is dict else None
    if type(events) is not list or not events:
        return out
    if result.get('outcome') in ('SKIPPED', 'NOT_REACHED', 'TIMED_OUT'):
        return dict(out, status='NO_COMPLETED_DEMONSTRATION_OPPORTUNITY')
    ids, candidate_texts = [], []
    for event in events:
        if type(event) is not dict:
            return out
        if event.get('actor') in ('host', 'native') and event.get('kind') in (
                'voice_error', 'capture_failed', 'transcription_failed', 'conversation_incomplete'):
            return dict(out, status='CAPTURE_INCOMPLETE', recording_health='FAILED')
        if event.get('actor') != 'candidate':
            continue
        payload = event.get('payload')
        text = payload.get('text') if type(payload) is dict else None
        if type(text) is not str or not text.strip() or type(event.get('id')) is not str or event['id'] in ids:
            return out
        ids.append(event['id'])
        candidate_texts.append(text)
    if not candidate_texts:
        return out
    out.update(source_event_ids=ids, record_sha256=_hash(result))
    if any(not (_only_code(text) or _bare_help(text)) for text in candidate_texts):
        return dict(out, status='SEMANTIC_REVIEW_REQUIRED')
    # A closed code-only answer demonstrates no recorded explanation. This
    # owner-requested practice convention does NOT turn missing execution into 0.
    out.update(status='NO_RECORDED_DEMONSTRATION', points=0,
               dimensions=[{'id': key, 'points': 0, 'maximum_points': weight,
                            'status': 'NO_RECORDED_DEMONSTRATION'} for key, weight in WEIGHTS.items()])
    out['sha256'] = _hash(out)
    return out
