"""S03-E2: replayable wall-elapsed time accounting for three-question rehearsal.

This is a LOCAL clock, not a certified anti-cheat source. Wall-clock deltas
include process downtime; monotonic host ticks prevent in-process time rollback.
Only the trusted Python host supplies samples. WebKit never supplies timestamps.
"""
import copy
import math

LIMIT_SECONDS = 45 * 60
QUESTION_LIMIT_SECONDS = 15 * 60
CLOCK_SCHEMA = 'tia-rehearsal-time/v1'


def finite_sample(value):
    return (type(value) in (float, int) and math.isfinite(value) and
            0 <= value <= 10 ** 12)


def begin(wall_seconds, host_tick, *, question_limit_seconds=None):
    if not finite_sample(wall_seconds) or not finite_sample(host_tick):
        raise ValueError('INVALID_CLOCK_SAMPLE')
    if question_limit_seconds not in (None, QUESTION_LIMIT_SECONDS):
        raise ValueError('INVALID_QUESTION_TIME_LIMIT')
    result = {
        'schema': CLOCK_SCHEMA, 'basis': 'LOCAL_WALL_AND_MONOTONIC_HOST',
        'integrity': 'LOCAL_UNATTESTED', 'limit_seconds': LIMIT_SECONDS,
        'started': False,
        'elapsed_seconds': 0.0, 'model_wait_seconds': 0.0,
        'last_wall_seconds': wall_seconds, 'last_host_tick': host_tick,
        'model_request_pending': False, 'current_question': 0, 'events': [],
        'questions': [
            {'index': index, 'elapsed_seconds': 0.0, 'model_wait_seconds': 0.0,
             'started': False, 'ended': False}
            for index in range(3)
        ],
    }
    if question_limit_seconds is not None:
        result['question_limit_seconds'] = question_limit_seconds
    return result


def advance(plan, wall_seconds, host_tick):
    """Advance only on a host command with persisted, replayable samples.

    Backwards clock adjustments >= 2 seconds freeze the rehearsal. Tiny wall
    changes are tolerated; monotonic elapsed still accounts for active time.
    """
    clock = plan.get('timing')
    if clock is None or plan['status'] != 'ACTIVE':
        return 'UNCHANGED'
    if not finite_sample(wall_seconds) or not finite_sample(host_tick):
        raise ValueError('INVALID_CLOCK_SAMPLE')
    wall_delta = wall_seconds - clock['last_wall_seconds']
    mono_delta = host_tick - clock['last_host_tick']
    if not clock['started']:
        clock['last_wall_seconds'] = wall_seconds
        clock['last_host_tick'] = host_tick
        return 'NOT_STARTED'
    if mono_delta < -0.0001:
        clock['integrity'] = 'MONOTONIC_ROLLBACK_HOLD'
        return 'CLOCK_HOLD'
    if wall_delta < -2.0:
        clock['integrity'] = 'WALL_ROLLBACK_HOLD'
        return 'CLOCK_HOLD'
    delta = max(0.0, wall_delta, mono_delta)
    if plan.get('continuity_policy') == 'tia-continuity/v3':
        # A new question receives its own full window only when presented. API
        # setup/reconnection between questions cannot consume a later window.
        current = clock['questions'][clock['current_question']]
        clock['last_wall_seconds'] = wall_seconds
        clock['last_host_tick'] = host_tick
        if not current['started']:
            return 'NOT_STARTED'
        delta = min(delta, max(0.0, QUESTION_LIMIT_SECONDS - current['elapsed_seconds']))
        current['elapsed_seconds'] = round(current['elapsed_seconds'] + delta, 6)
        clock['elapsed_seconds'] = round(clock['elapsed_seconds'] + delta, 6)
        if clock['model_request_pending']:
            current['model_wait_seconds'] = round(current['model_wait_seconds'] + delta, 6)
            clock['model_wait_seconds'] = round(clock['model_wait_seconds'] + delta, 6)
        return 'QUESTION_TIMEOUT' if current['elapsed_seconds'] >= QUESTION_LIMIT_SECONDS else 'ACTIVE'
    # Only the time through the hard deadline counts as interview time.
    delta = min(delta, max(0.0, LIMIT_SECONDS - clock['elapsed_seconds']))
    clock['last_wall_seconds'] = wall_seconds
    clock['last_host_tick'] = host_tick
    if delta > 0:
        clock['elapsed_seconds'] = round(clock['elapsed_seconds'] + delta, 6)
        q = clock['questions'][clock['current_question']]
        if q['started']:
            q['elapsed_seconds'] = round(q['elapsed_seconds'] + delta, 6)
        if clock['model_request_pending']:
            clock['model_wait_seconds'] = round(clock['model_wait_seconds'] + delta, 6)
            q['model_wait_seconds'] = round(q['model_wait_seconds'] + delta, 6)
    if clock['elapsed_seconds'] >= LIMIT_SECONDS:
        return 'TIMEOUT'
    if clock.get('question_limit_seconds') == QUESTION_LIMIT_SECONDS and clock['questions'][clock['current_question']]['elapsed_seconds'] >= QUESTION_LIMIT_SECONDS:
        return 'QUESTION_TIMEOUT'
    return 'ACTIVE'


def event(plan, kind, *, evidence_id=None):
    clock = plan.get('timing')
    if clock is None or (plan.get('continuity_policy') != 'tia-continuity/v3' and len(clock['events']) >= 480):
        return
    item = {'id': 'timing-' + str(len(clock['events']) + 1),
            'kind': kind, 'question_index': clock['current_question'],
            'elapsed_seconds': clock['elapsed_seconds'],
            'model_wait_seconds': clock['model_wait_seconds']}
    if evidence_id is not None:
        item['source_event_id'] = evidence_id
    clock['events'].append(item)

def start_on_question_presented(plan, wall_seconds, host_tick, *, evidence_id=None):
    clock = plan.get('timing')
    if clock is None:
        return
    if clock.get('question_limit_seconds') == QUESTION_LIMIT_SECONDS:
        current = clock['questions'][clock['current_question']]
        if current['started']:
            return
        if not finite_sample(wall_seconds) or not finite_sample(host_tick):
            raise ValueError('INVALID_CLOCK_SAMPLE')
        clock['started'] = True
        clock['last_wall_seconds'] = wall_seconds
        clock['last_host_tick'] = host_tick
        current['started'] = True
        event(plan, 'FIRST_QUESTION_PRESENTED' if clock['current_question'] == 0 else 'QUESTION_PRESENTED', evidence_id=evidence_id)
        return
    if clock['started']:
        return
    if not finite_sample(wall_seconds) or not finite_sample(host_tick):
        raise ValueError('INVALID_CLOCK_SAMPLE')
    clock['started'] = True
    clock['last_wall_seconds'] = wall_seconds
    clock['last_host_tick'] = host_tick
    clock['questions'][clock['current_question']]['started'] = True
    event(plan, 'FIRST_QUESTION_PRESENTED', evidence_id=evidence_id)

def request_started(plan):
    if plan.get('timing') and plan['status'] == 'ACTIVE':
        plan['timing']['model_request_pending'] = True
        event(plan, 'MODEL_REQUEST_STARTED')


def request_finished(plan):
    if plan.get('timing'):
        plan['timing']['model_request_pending'] = False


def close_question(plan, *, outcome='SUBMITTED'):
    clock = plan.get('timing')
    if clock is None:
        return None
    if clock['model_request_pending']:
        raise ValueError('NATIVE_REQUEST_PENDING')
    current = clock['questions'][clock['current_question']]
    current['ended'] = True
    event(plan, 'QUESTION_' + outcome)
    evidence = {k: current[k] for k in ('elapsed_seconds', 'model_wait_seconds')}
    if clock['current_question'] < 2:
        clock['current_question'] += 1
        if clock.get('question_limit_seconds') == QUESTION_LIMIT_SECONDS:
            clock['questions'][clock['current_question']]['started'] = False
            event(plan, 'NEXT_QUESTION_QUEUED')
        else:
            clock['questions'][clock['current_question']]['started'] = clock['started']
            event(plan, 'NEXT_QUESTION_PRESENTED')
    return evidence


def final_metrics(plan):
    clock = plan.get('timing')
    if clock is None:
        return None
    return {
        'basis': clock['basis'], 'integrity': clock['integrity'],
        'started': clock['started'],
        'limit_seconds': LIMIT_SECONDS,
        'elapsed_seconds': clock['elapsed_seconds'],
        'model_wait_seconds': clock['model_wait_seconds'],
        'candidate_and_other_seconds': max(0, round(clock['elapsed_seconds'] - clock['model_wait_seconds'], 6)),
        'questions': [copy.deepcopy(q) for q in clock['questions']],
        'events': copy.deepcopy(clock['events']),
        'certified': False,
    }
