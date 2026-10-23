"""S03-E3C-A: offline evidence-anchored training assignments and review contract.

A training suggestion is *not* an AI assessment or a certified ability gap.
The complete immutable rehearsal is the sole source. No SQL, network, provider,
score writes, journal migration or transcript synthesis occurs in this module.
"""
from __future__ import annotations

import hashlib
import json
import re
from .evidence_scorecard import build_scorecard
from .communication_rubric import build_communication_evidence

SCHEMA = 'tia-grounded-trainer/v1'
PROPOSAL_SCHEMA = 'tia-trainer-model-proposal/v1'
SHA = re.compile(r'[0-9a-f]{64}\Z')
TAGS = frozenset(('VERSION_RECHECK', 'SQL_DIAGNOSTIC', 'SQL_FIRST_ATTEMPT',
                  'LOCAL_FIXTURE_COVERAGE', 'TESTING_PRACTICE', 'CLOSING_PRACTICE'))


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def _make_drill(idx, q, *, tag, trigger, priority, action, check, why, latest_sql_event_id=None):
    a = q['accuracy']
    ids = q.get('behavior', {}).get('evidence_event_ids', []) if q.get('behavior') else []
    tied = a.get('candidate_event_id')
    # The latest SQL receipt binds an event id only if it still exists in the
    # authentic saved per-question candidate-event list.
    citations = [tied] if tied and tied in ids else []
    if tag == 'VERSION_RECHECK' and latest_sql_event_id in ids and latest_sql_event_id not in citations:
        # Cite BOTH the tested historical SQL and the new, unverified SQL event.
        citations.append(latest_sql_event_id)
    if not citations and ids:  # observed actions are not proof of skill quality
        citations = ids[-1:]
    return {
        'id': 'Q%d-%s' % (idx + 1, tag), 'priority': priority, 'question_index': idx,
        'skill_tag': tag, 'trigger': trigger,
        'interpretation': 'TRAINING_OPPORTUNITY_NOT_COMPETENCY_DIAGNOSIS',
        'evidence': {
            'question_sha256': q['question_sha256'],
            'candidate_event_ids': citations, 'fixture_sha256': a.get('fixture_sha256'),
            'observed_local_status': a['status'], 'observed_reason': a['reason'],
        },
        'rationale': why, 'task': action, 'acceptance': check,
        'fresh_retest_required': True,
        'completion': 'NOT_ATTEMPTED',
    }


def build_grounded_trainer(plan):
    """Read-only projection. Missing observations remain unknown, not zero."""
    technical = build_scorecard(plan)
    communication = build_communication_evidence(plan)
    complete = plan.get('status') != 'ACTIVE'
    candidates = []
    if complete:
        for q in technical['questions']:
            i = q['index']
            a = q['accuracy']
            status, reason = a['status'], a['reason']
            count = (q.get('behavior') or {}).get('sql_submissions', 0)
            events = ((plan['results'][i].get('session') or {}).get('events') or []) if i < len(plan.get('results', [])) and type(plan['results'][i]) is dict else []
            implementations = [e.get('id') for e in events if type(e) is dict and e.get('actor') == 'candidate'
                               and e.get('kind') == 'implement' and type(e.get('id')) is str]
            latest = implementations[-1] if implementations else None
            if reason in ('TESTED_PRIOR_SQL_VERSION', 'GRADE_SQL_HASH_MISMATCH', 'GRADE_EVIDENCE_MISMATCH', 'GRADE_SUBMISSION_NOT_FOUND', 'QUESTION_SKIPPED_AFTER_TEST'):
                candidates.append(_make_drill(i, q, tag='VERSION_RECHECK', trigger=reason, priority=1,
                    latest_sql_event_id=latest,
                    why='A local fixture receipt does not certify the latest candidate SQL.',
                    action='Review the latest SQL event and rerun an explicitly approved local fixture against exactly that version.',
                    check='Record the latest SQL event hash, fixture hash and new execution receipt; do not carry forward an older PASS.'))
            elif status == 'FAILED':
                candidates.append(_make_drill(i, q, tag='SQL_DIAGNOSTIC', trigger='FAILED_LOCAL_FIXTURE', priority=1,
                    why='One approved local fixture produced a mismatch; its root cause is not yet established.',
                    action='Explain the observed versus expected row shape; isolate one minimal case and revise the query.',
                    check='On an independently approved local fixture, document the original mismatch, changed SQL hash and new outcome.'))
            elif status == 'EXECUTION_ERROR':
                candidates.append(_make_drill(i, q, tag='SQL_DIAGNOSTIC', trigger='EXECUTION_ERROR', priority=1,
                    why='The approved local attempt had an execution error; that is not a competency score.',
                    action='Reproduce the local error, classify syntax/schema/resource cause, and make one bounded correction.',
                    check='Re-execute under approved local PostgreSQL isolation and capture actual error or resulting rows.'))
            elif status == 'NOT_VERIFIED' and count:
                candidates.append(_make_drill(i, q, tag='TESTING_PRACTICE', trigger=reason, priority=2,
                    why='The final submitted SQL has no currently attributable passing or failing fixture receipt.',
                    action='Create a small reviewed edge-case fixture and explicitly request native local execution.',
                    check='Capture a fixture hash and the result bound to the latest SQL event; no hidden-test claim.'))
            elif status == 'PASSED':
                candidates.append(_make_drill(i, q, tag='LOCAL_FIXTURE_COVERAGE', trigger='ONE_LOCAL_FIXTURE_PASSED', priority=3,
                    why='A single approved local fixture passed; general correctness remains unverified.',
                    action='Identify two new edge cases, with at least one tie or NULL scenario if relevant, and author independently checked expected rows.',
                    check='Explain expected rows before execution, test with consent and record each new receipt; never call these official hidden tests.'))
            elif q.get('outcome') != 'NOT_REACHED':
                candidates.append(_make_drill(i, q, tag='SQL_FIRST_ATTEMPT', trigger='NO_VERIFIED_SQL_OBSERVATION', priority=4,
                    why='There is insufficient SQL execution evidence for this question.',
                    action='Try a fresh independently selected comparable question; articulate a plan, write a first SQL attempt and test it.',
                    check='Submit an actual SQL event and at least one independently reviewed local test; record outcomes without grading ability.'))
        # C06 remains uncovered by app instrumentation: this is a data-coverage
        # drill, not a claim that the candidate has poor closing etiquette.
        if all(q['dimensions'][5]['status'] == 'NOT_OBSERVED' for q in communication['questions']):
            candidates.append({
                'id': 'GENERAL-CLOSING_PRACTICE', 'priority': 5, 'question_index': None,
                'skill_tag': 'CLOSING_PRACTICE', 'trigger': 'C06_NOT_OBSERVED',
                'interpretation': 'NOT_OBSERVED_NOT_A_DEFICIT',
                'evidence': {'question_sha256': None, 'candidate_event_ids': [],
                             'fixture_sha256': None, 'observed_local_status': 'NOT_APPLICABLE',
                             'observed_reason': 'NO_EXPLICIT_CLOSING_SPEECH_EVENT'},
                'rationale': 'The current app does not record a dedicated closing statement. No C06 quality finding is possible.',
                'task': 'Practice an optional 45-second factual summary: scope, current test result, unresolved limits and next verification step.',
                'acceptance': 'In a NEW practice recording, explicitly identify what was and was not verified; do not reuse Finish button as evidence.',
                'fresh_retest_required': True, 'completion': 'NOT_ATTEMPTED',
            })
    candidates.sort(key=lambda d: (d['priority'], d['question_index'] if d['question_index'] is not None else 3, d['id']))
    output = {
        'schema': SCHEMA, 'mode': 'OFFLINE_EVIDENCE_DRILLS',
        'status': 'READY_FOR_HUMAN_REVIEW' if complete else 'AWAITING_LOCKED_INTERVIEW',
        'sources': {'technical_sha256': technical['sha256'],
                    'communication_sha256': communication['sha256']},
        'drills': candidates[:3] if complete else [],
        'candidate_drill_count': len(candidates) if complete else 0,
        'primary_drill_id': candidates[0]['id'] if complete and candidates else None,
        'numeric_scores': 'NOT_SCORED',
        'model_assessment': 'NOT_REQUESTED', 'paid_provider_requests': 0,
        'next_question_policy': 'FRESH_HELD_OUT_SKILL_MATCHED_NO_SAME_QUESTION_REUSE',
        'limitations': [
            'This is an offline exercise recommendation based on observations, not a model diagnosis.',
            'Unknown observations are not negative skill findings.',
            'One local fixture is not official hidden-test coverage or a competency percentage.',
            'A saved receipt checksum is not a cryptographic attestation.',
            'No causal learning gain, skill score, or weighted hiring grade is inferred.',
            'Future paid AI advice requires separate native consent and human review.',
        ],
    }
    output['sha256'] = _sha(output)
    return output


def validate_trainer_model_proposal(proposal, trainer):
    """Validate a potential AI draft without treating it as approved advice.

    Syntactic/citation validation cannot establish semantic truth. The caller
    must show this as a model *proposal* requiring independent human review.
    """
    if type(trainer) is not dict or trainer.get('schema') != SCHEMA or trainer.get('sha256') != _sha({
            k: v for k, v in trainer.items() if k != 'sha256'}):
        raise ValueError('INVALID_TRAINER_SOURCE')
    if trainer['status'] != 'READY_FOR_HUMAN_REVIEW':
        raise ValueError('TRAINER_NOT_READY')
    keys = {'schema', 'trainer_sha256', 'assessor_kind', 'drill_id', 'question_index',
            'skill_tag', 'cited_candidate_events', 'cited_fixture_sha256',
            'hypothesis', 'training_action', 'acceptance', 'uncertainty'}
    if type(proposal) is not dict or set(proposal) != keys or proposal.get('schema') != PROPOSAL_SCHEMA:
        raise ValueError('INVALID_TRAINER_PROPOSAL')
    if proposal['trainer_sha256'] != trainer['sha256'] or proposal['assessor_kind'] != 'MODEL_PROPOSAL':
        raise ValueError('UNAUTHORIZED_TRAINER_PROPOSAL')
    drill = next((d for d in trainer['drills'] if d['id'] == proposal['drill_id']), None)
    if (not drill or type(proposal['question_index']) is not type(drill['question_index'])
            or proposal['question_index'] != drill['question_index']
            or proposal['skill_tag'] != drill['skill_tag']):
        raise ValueError('UNKNOWN_TRAINING_DRILL')
    refs = proposal['cited_candidate_events']
    if (type(refs) is not list or len(refs) > 4 or len(refs) != len(set(str(x) for x in refs))
            or any(type(x) is not str or x not in drill['evidence']['candidate_event_ids'] for x in refs)
            or refs != drill['evidence']['candidate_event_ids']):
        raise ValueError('UNSUPPORTED_TRAINER_CITATION')
    if proposal['cited_fixture_sha256'] != drill['evidence']['fixture_sha256']:
        raise ValueError('UNSUPPORTED_TRAINER_FIXTURE')
    for k, minimum, maximum in [('hypothesis', 20, 700), ('training_action', 30, 900),
                                ('acceptance', 20, 800), ('uncertainty', 20, 500)]:
        value = proposal[k]
        if type(value) is not str or not minimum <= len(value.strip()) <= maximum or '\x00' in value:
            raise ValueError('INVALID_TRAINER_TEXT')
    return {'schema': PROPOSAL_SCHEMA, 'status': 'PENDING_HUMAN_REVIEW',
            'authority': 'NONE', 'trainer_sha256': trainer['sha256'],
            'drill_id': drill['id'], 'cited_candidate_events': list(refs),
            'authoritative_score': 'NOT_SCORED', 'validated_semantic_quality': False}
