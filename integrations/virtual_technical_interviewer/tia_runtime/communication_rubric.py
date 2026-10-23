"""E3-B: source-cited communication evidence, not inferred communication talent.

A deterministic, read-only projection of frozen candidate/interviewer events.
No model, database or network call; no saved-state mutation, numeric rating,
personality judgement, or 60/40 weighted hiring score. A validated *proposal*
can be prepared for future review, but never becomes a score by this module.
"""
from __future__ import annotations

import hashlib
import math
import json
import re

SCHEMA = 'tia-communication-evidence/v1'
RUBRIC = 'tia-communication-rubric-proposal/v0.3'
PROPOSAL_SCHEMA = 'tia-communication-review-proposal/v1'
CANDIDATE_KINDS = frozenset(('clarify', 'plan', 'implement', 'test', 'help'))

# Proposed weights from PRD v3 §14A; NOT approved/calibrated numeric scores.
DIMENSIONS = (
    ('C01', 'Clarification and expectation alignment', 6, ('clarify',)),
    ('C02', 'Explainable plan and in-flight narration', 7, ('plan',)),
    ('C03', 'Progress and evidence narrative', 7, ('test', 'plan')),
    ('C04', 'Gap-to-action translation and bounded assistance', 9, ('help',)),
    ('C05', 'Feedback integration and collaboration-to-execution', 7, ()),
    ('C06', 'Professional closure and honest synthesis', 4, ()),
)
ANCHORS = {
    '0': 'Observed counterexample/ineffective behavior (requires contextual review)',
    '1': 'Required repeated prompting',
    '2': 'Partly demonstrated',
    '3': 'Independently adequate',
    '4': 'Independently robust in an unfamiliar case',
}


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _candidate_events(session):
    """Return bounded authentic event references, never read model-generated claims as candidate speech."""
    if type(session) is not dict or type(session.get('events')) is not list:
        return []
    evidence = []
    ids = set()
    for position, item in enumerate(session['events'][:512]):
        if (type(item) is not dict or item.get('actor') != 'candidate'
                or item.get('kind') not in CANDIDATE_KINDS):
            continue
        eid = item.get('id')
        payload = item.get('payload')
        if (type(eid) is not str or not eid or eid in ids or type(payload) is not dict
                or type(payload.get('text')) is not str):
            continue
        content = payload['text']
        if not content.strip():
            continue
        ids.add(eid)
        elapsed = item.get('elapsed_seconds')
        elapsed = (round(elapsed, 6) if type(elapsed) in (int, float) and
                   math.isfinite(elapsed) and elapsed >= 0 else None)
        evidence.append({
            'event_id': eid, 'position': position, 'kind': item['kind'],
            'elapsed_seconds': elapsed,
            'candidate_text_sha256': hashlib.sha256(content.encode('utf-8')).hexdigest(),
            # The source export already includes the full text. A bounded preview
            # here lets a reviewer locate the exact utterance without duplicating SQL.
            'preview': re.sub(r'[\x00-\x1f\x7f]', ' ', content).strip()[:180],
        })
    return evidence


def _interviewer_reply_positions(session):
    if type(session) is not dict or type(session.get('events')) is not list:
        return []
    positions = []
    for i, e in enumerate(session['events'][:512]):
        if (type(e) is dict and e.get('actor') == 'interviewer'
                and e.get('provenance') == 'LIVE_MODEL' and type(e.get('payload')) is dict
                and e['payload'].get('operation') == 'reply'
                and type(e.get('id')) is str):
            positions.append({'position': i, 'event_id': e['id']})
    return positions


def _question_observations(index, source_record):
    session = source_record.get('session') if type(source_record) is dict else None
    candidates = _candidate_events(session)
    replies = _interviewer_reply_positions(session)
    dims = []
    for dim_id, title, max_pts, relevant in DIMENSIONS:
        matching = [c for c in candidates if c['kind'] in relevant]
        pairings = []
        if dim_id == 'C05':
            # Chronological follow-up != semantic uptake. A model rater must
            # examine the actual reply and subsequent action before making a claim.
            for reply in replies:
                later = next((c for c in candidates if c['position'] > reply['position']
                              and c['kind'] in ('plan', 'implement', 'test')), None)
                if later is not None:
                    pairings.append({'interviewer_event_id': reply['event_id'],
                                     'candidate_event_id': later['event_id']})
            refs = [c for c in candidates if any(p['candidate_event_id'] == c['event_id']
                                                 for p in pairings)]
        elif dim_id == 'C06':
            # 'Submit question' is a host control, not a dedicated candidate
            # closing statement. No credible closing-speech event exists yet.
            refs = []
        else:
            refs = matching
        has_refs = bool(refs)
        dims.append({
            'id': dim_id, 'title': title, 'proposed_max_points': max_pts,
            'status': 'POTENTIAL_EVIDENCE_NEEDS_SEMANTIC_REVIEW' if has_refs else 'NOT_OBSERVED',
            'rating_status': 'NOT_EVALUATED', 'anchor_0_to_4': None,
            'provisional_points': None, 'confidence': 'NOT_ASSESSED',
            'evidence': [{k: x[k] for k in ('event_id', 'kind', 'elapsed_seconds', 'candidate_text_sha256', 'preview')}
                         for x in refs[:4]],
            'total_candidate_refs': len(refs),
            'followup_sequences': pairings[:4] if dim_id == 'C05' else [],
            'observation_limit': ('KIND_ONLY_NOT_SEMANTIC_QUALITY' if dim_id not in ('C05', 'C06')
                                  else 'SEQUENCE_DOES_NOT_PROVE_INTEGRATION' if dim_id == 'C05'
                                  else 'NO_EXPLICIT_CLOSING_SPEECH_EVENT'),
        })
    return {
        'index': index,
        'closed': source_record is not None,
        'outcome': source_record.get('outcome') if type(source_record) is dict else None,
        'candidate_event_count': len(candidates),
        'interviewer_reply_count': len(replies),
        'dimensions': dims,
    }


def build_communication_evidence(plan):
    """Projection strictly from immutable rehearsal records; safe during journal replay."""
    if (type(plan) is not dict or type(plan.get('questions')) is not list
            or len(plan['questions']) != 3 or type(plan.get('results', [])) is not list
            or len(plan.get('results', [])) > 3):
        raise ValueError('INVALID_COMMUNICATION_SOURCE')
    results = plan.get('results', [])
    questions = [_question_observations(i, results[i] if i < len(results) else None)
                 for i in range(3)]
    counts = {'clarifications': 0, 'plans': 0, 'help_requests': 0, 'test_descriptions': 0,
              'implement_submissions': 0, 'interviewer_replies': 0}
    for i, q in enumerate(questions):
        source = results[i].get('session') if i < len(results) and type(results[i]) is dict else None
        events = _candidate_events(source)
        for event in events:
            key = {'clarify': 'clarifications', 'plan': 'plans', 'help': 'help_requests',
                   'test': 'test_descriptions', 'implement': 'implement_submissions'}[event['kind']]
            counts[key] += 1
        counts['interviewer_replies'] += q['interviewer_reply_count']
    output = {
        'schema': SCHEMA, 'rubric_version': RUBRIC,
        'status': 'FINAL_EVIDENCE_VIEW' if plan.get('status') != 'ACTIVE' else 'IN_PROGRESS',
        'source': 'CANDIDATE_AND_VERIFIED_INTERVIEWER_EVENTS_ONLY',
        'proposed_weight_policy': {'technical': 60, 'communication': 40,
                                   'status': 'UNCALIBRATED_HYPOTHESIS_NOT_APPLIED'},
        'anchor_proposal': ANCHORS,
        'questions': questions,
        'summary': {
            'closed_questions': len(results), 'total_questions': 3,
            'observed_action_counts': counts,
            'evidence_candidate_dimensions': sum(d['status'] != 'NOT_OBSERVED' for q in questions
                                                 for d in q['dimensions']),
            'evaluated_dimensions': 0,
            'communication_competency': 'NOT_SCORED',
            'overall_grade': 'NOT_SCORED',
            'suggested_mental_impression_bonus': 'NOT_ENABLED',
        },
        'limitations': [
            'Event kinds and excerpts are evidence candidates, NOT demonstrations of communication quality.',
            'A model reply followed by a new candidate action does not prove understanding or improvement.',
            'No validated 0-4 anchor or communication points have been awarded.',
            'An unobserved dimension is NOT_OBSERVED, never an automatic zero.',
            'Current app has no explicit closing-speech event for C06.',
            'Accent, personality, emotion and demographics are excluded.',
            'Results are local rehearsal feedback, not an employer or hiring decision.',
        ],
    }
    output['sha256'] = _digest(output)
    return output


def validate_review_proposal(proposal, evidence):
    """Strict interface for *future* assessor drafts, not an approval/scoring API.

    Reject model-supplied text/IDs that do not appear in the Host evidence view.
    The result always remains PENDING_HUMAN_REVIEW and awards zero final points.
    """
    if type(evidence) is not dict or evidence.get('schema') != SCHEMA or evidence.get('sha256') != _digest({
            k: v for k, v in evidence.items() if k != 'sha256'}):
        raise ValueError('INVALID_EVIDENCE_SOURCE')
    if (type(proposal) is not dict or set(proposal) != {
            'schema', 'rubric_version', 'evidence_sha256', 'assessor_kind', 'question_index',
            'dimension_id', 'anchor', 'cited_candidate_events', 'reason'} or
            proposal['schema'] != PROPOSAL_SCHEMA or proposal['rubric_version'] != RUBRIC or
            proposal['evidence_sha256'] != evidence['sha256'] or
            proposal['assessor_kind'] not in ('HUMAN_DRAFT', 'MODEL_PROPOSAL')):
        raise ValueError('INVALID_REVIEW_PROPOSAL')
    idx = proposal['question_index']
    if type(idx) is not int or not 0 <= idx < 3:
        raise ValueError('INVALID_REVIEW_QUESTION')
    dim = next((d for d in evidence['questions'][idx]['dimensions']
                if d['id'] == proposal['dimension_id']), None)
    if dim is None or dim['status'] == 'NOT_OBSERVED':
        raise ValueError('NO_OBSERVED_DIMENSION')
    anchor = proposal['anchor']
    if type(anchor) is not int or not 0 <= anchor <= 4:
        raise ValueError('INVALID_REVIEW_ANCHOR')
    ids = proposal['cited_candidate_events']
    allowed = {e['event_id'] for e in dim['evidence']}
    if type(ids) is not list or not ids or len(ids) > 4 or any(type(x) is not str for x in ids) or len(set(ids)) != len(ids) or not set(ids) <= allowed:
        raise ValueError('UNCITED_OR_CROSS_QUESTION_EVIDENCE')
    reason = proposal['reason']
    if type(reason) is not str or not 24 <= len(reason.strip()) <= 1200:
        raise ValueError('UNSUPPORTED_REVIEW_REASON')
    # Even a syntactically valid proposal has no independent scoring authority.
    return {
        'schema': PROPOSAL_SCHEMA,
        'status': 'PENDING_HUMAN_REVIEW',
        'provisional': True, 'rated_dimension': dim['id'],
        'question_index': idx, 'proposed_anchor': anchor,
        'proposed_points': None,
        'cited_candidate_events': list(ids),
        'evidence_sha256': evidence['sha256'],
        'authoritative_communication_score': 'NOT_SCORED',
    }
