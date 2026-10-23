"""S03-E3D: host-owned seven-day SMART rehearsal plan and self-reported activity log.

A plan is a deterministic projection of immutable interview evidence, not a skill
assessment. User-entered progress can never certify a performance improvement,
a fixture result, or a human-reviewed model proposal.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re

from .grounded_trainer import build_grounded_trainer

SCHEMA = 'tia-smart-improvement-plan/v1'
PROGRESS_SCHEMA = 'tia-smart-progress/v1'
SHA = re.compile(r'[0-9a-f]{64}\Z')
KINDS = frozenset(('PRACTICED', 'BLOCKED', 'RETEST_RECORDED'))
DAY = 86400


class SmartPlanError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _sha(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def build_smart_plan(rehearsal):
    """No I/O or timestamps: same frozen interview => exact same plan."""
    trainer = build_grounded_trainer(rehearsal)
    goals = []
    for i, drill in enumerate(trainer['drills']):
        days = (1, 3, 7)[min(i, 2)]
        # Drill fields are source-linked observations, not assessed competencies.
        goals.append({
            'id': 'SMART-' + drill['id'],
            'drill_id': drill['id'], 'priority': drill['priority'],
            'question_index': drill['question_index'], 'skill_tag': drill['skill_tag'],
            'source': {
                'trainer_sha256': trainer['sha256'], 'trigger': drill['trigger'],
                'question_sha256': drill['evidence']['question_sha256'],
                'candidate_event_ids': copy.deepcopy(drill['evidence']['candidate_event_ids']),
                'fixture_sha256': drill['evidence']['fixture_sha256'],
            },
            'specific': drill['task'],
            'measurable': drill['acceptance'],
            'achievable': 'One bounded practice task; record an attempt or blocker rather than claiming proficiency.',
            'relevant': 'Source-linked %s training opportunity, not a verified competency deficit.' % drill['skill_tag'],
            'time_bound': {'days_after_explicit_start': days, 'duration_minutes_suggested': (25, 35, 45)[min(i, 2)]},
            'verification': {
                'practice_log': 'SELF_REPORTED_ONLY',
                'fresh_retest': 'NEW_INDEPENDENT_TEST_REQUIRED',
                'improvement': 'NOT_ESTABLISHED',
            },
        })
    result = {
        'schema': SCHEMA, 'status': ('READY_TO_START' if trainer['status'] == 'READY_FOR_HUMAN_REVIEW'
                                    else 'AWAITING_LOCKED_INTERVIEW'),
        'trainer_sha256': trainer['sha256'],
        # Bind the plan to the complete frozen source, even when a trainer drill
        # happens to cite unchanged event IDs after candidate text is modified.
        'rehearsal_sha256': _sha(rehearsal),
        'origin': 'DETERMINISTIC_OFFLINE_EVIDENCE',
        'days_in_sprint': 7,
        'goals': goals,
        'numeric_competency_score': 'NOT_SCORED',
        'improvement_certification': 'NOT_ESTABLISHED',
        'limits': ['Deadlines begin only on an explicit Host-recorded start.',
                   'Practice logs and user-supplied artifact hashes are self-reported, not checked against a database.',
                   'A fresh independently authorized retest and review are required before making improvement claims.',
                   'A model proposal awaiting human review does not authorize or alter this plan.'],
    }
    result['sha256'] = _sha(result)
    return result


def start_smart_progress(plan, host_wall_seconds):
    if plan.get('status') != 'READY_TO_START' or not plan['goals']:
        raise SmartPlanError('SMART_PLAN_NOT_READY')
    if type(host_wall_seconds) not in (int, float) or not math.isfinite(host_wall_seconds) or not 0 <= host_wall_seconds <= 1e12:
        raise SmartPlanError('INVALID_HOST_START_TIME')
    started = round(host_wall_seconds, 6)
    out = {'schema': PROGRESS_SCHEMA, 'plan_sha256': plan['sha256'],
           'started_wall_seconds': started,
           'deadlines': {g['id']: round(started + DAY * g['time_bound']['days_after_explicit_start'], 6)
                         for g in plan['goals']},
           'entries': [], 'completion_authority': 'SELF_REPORTED_NOT_VERIFIED',
           'ability_improved': 'NOT_ESTABLISHED'}
    out['sha256'] = _sha(out)
    return out


def record_smart_activity(plan, progress, *, task_id, kind, note, artifact_sha256, host_wall_seconds):
    """Append-only bounded log. Artifact hash is a *claim*, not verified bytes."""
    if type(progress) is not dict or progress.get('schema') != PROGRESS_SCHEMA or progress.get('plan_sha256') != plan.get('sha256'):
        raise SmartPlanError('SMART_PLAN_SOURCE_CHANGED')
    expected = _sha({k: v for k, v in progress.items() if k != 'sha256'})
    if progress.get('sha256') != expected:
        raise SmartPlanError('SMART_PROGRESS_CORRUPTED')
    if type(task_id) is not str or task_id not in {g['id'] for g in plan['goals']}:
        raise SmartPlanError('UNKNOWN_SMART_TASK')
    if type(kind) is not str or kind not in KINDS:
        raise SmartPlanError('INVALID_SMART_EVENT')
    if type(note) is not str or not 3 <= len(note.strip()) or len(note.encode('utf-8')) > 500 or '\x00' in note:
        raise SmartPlanError('INVALID_SMART_NOTE')
    if artifact_sha256 is not None and (type(artifact_sha256) is not str or not SHA.fullmatch(artifact_sha256)):
        raise SmartPlanError('INVALID_SMART_ARTIFACT')
    if (kind == 'RETEST_RECORDED') != (artifact_sha256 is not None):
        raise SmartPlanError('SMART_RETEST_REQUIRES_ARTIFACT_HASH')
    if type(host_wall_seconds) not in (int, float) or not math.isfinite(host_wall_seconds) or host_wall_seconds < progress['started_wall_seconds'] - 2:
        raise SmartPlanError('INVALID_SMART_EVENT_TIME')
    prior = progress['entries']
    if len(prior) >= 24 or sum(e['task_id'] == task_id for e in prior) >= 8:
        raise SmartPlanError('SMART_HISTORY_LIMIT')
    new = copy.deepcopy(progress)
    new['entries'].append({'ordinal': len(prior) + 1, 'task_id': task_id, 'kind': kind,
                           'note': note.strip(), 'artifact_sha256': artifact_sha256,
                           'host_wall_seconds': round(host_wall_seconds, 6),
                           'verification': 'SELF_REPORTED_UNVERIFIED',
                           'ability_improved': 'NOT_ESTABLISHED'})
    new.pop('sha256')
    new['sha256'] = _sha(new)
    return new


def smart_progress_summary(plan, progress):
    if progress is None:
        return {'status': 'NOT_STARTED', 'goals': [], 'recorded_attempts': 0,
                'independently_verified_improvements': 0}
    if progress.get('plan_sha256') != plan['sha256'] or progress.get('sha256') != _sha({k: v for k, v in progress.items() if k != 'sha256'}):
        raise SmartPlanError('SMART_PROGRESS_CORRUPTED')
    goals = []
    for goal in plan['goals']:
        entries = [e for e in progress['entries'] if e['task_id'] == goal['id']]
        goals.append({'id': goal['id'], 'due_wall_seconds': progress['deadlines'][goal['id']],
                      'attempts': len(entries),
                      'latest_activity': entries[-1]['kind'] if entries else 'NOT_ATTEMPTED',
                      'completion': 'AWAITING_INDEPENDENT_RETEST',
                      'independently_verified_improvement': False})
    return {'status': 'STARTED', 'goals': goals,
            'recorded_attempts': len(progress['entries']),
            'independently_verified_improvements': 0}
