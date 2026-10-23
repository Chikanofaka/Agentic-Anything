"""S03-E1: bounded, unscored three-question AI rehearsal plan.

This module creates an immutable question allocation. Native authorization,
conversation transactions and receipt sealing remain in the existing host and
controller. No correctness or performance grading is performed here.
"""
import copy


class RehearsalError(ValueError):
    pass


MAX_REHEARSAL_TURNS = 4


def question_from_review(review):
    fields = review['fields']
    return {
        'id': review['question_id'],
        'title': ((review.get('extraction') or {}).get('title') or {}).get('text') or 'User-submitted question',
        'statement': fields['problem_statement'] + '\n\nTask: ' + fields['task'],
        'schema': fields['schema'],
        'example_input': fields.get('example_input', ''),
        'expected_output': fields.get('expected_output', ''),
        'constraints': fields.get('constraints', ''),
        'difficulty': (review.get('extraction') or {}).get('declared_difficulty') or 'UNVERIFIED',
        'environment': fields['environment'],
        'source': fields['source'],
        'content_sha256': review['content_sha256'],
        'practice_only': True,
    }


def create_plan(config, reviews):
    if (config is None or config.duration_minutes != 45 or config.question_count != 3
            or config.question_source != 'BYOQ' or len(reviews) != 3):
        raise RehearsalError('REHEARSAL_REQUIRES_THREE_QUESTIONS')
    if (any(not item.get('human_confirmed') or not item.get('practice_eligible')
            or item['fields'].get('environment') != config.technical_environment for item in reviews)
            or len({item['content_sha256'] for item in reviews}) != 3):
        raise RehearsalError('REHEARSAL_QUESTIONS_NOT_CONFIRMED')
    questions = [question_from_review(item) for item in reviews]
    return {
        'schema': 'tia-three-question-rehearsal/v1',
        'status': 'ACTIVE',
        'current_index': 0,
        'questions': copy.deepcopy(questions),
        'results': [],
        'max_turns_per_question': MAX_REHEARSAL_TURNS,
        'technical': 'NOT_SCORED', 'communication': 'NOT_SCORED',
        'execution': 'NOT_RUN',
        'formal_exam_authorized': False,
    }


def public_plan(plan):
    if plan is None:
        return None
    return {
        'schema': plan['schema'], 'status': plan['status'],
        'current_index': plan['current_index'],
        'question_count': len(plan['questions']),
        'max_turns_per_question': plan['max_turns_per_question'],
        'questions': [
            {'title': q['title'], 'source': q['source'], 'environment': q['environment'],
             'difficulty': q['difficulty'], 'content_sha256': q['content_sha256'],
             'status': (plan['results'][i]['outcome'] if i < len(plan['results']) else
                        'CURRENT' if i == plan['current_index'] and plan['status'] == 'ACTIVE'
                        else 'PENDING')}
            for i, q in enumerate(plan['questions'])
        ],
        'results': copy.deepcopy(plan['results']),
        **({'timing': copy.deepcopy(plan['timing'])} if plan.get('timing') else {}),
        'technical': 'NOT_SCORED', 'communication': 'NOT_SCORED',
        'execution': ('SOME_LOCAL_FIXTURES_RUN' if any(x.get('correctness') == 'VERIFIED_LOCAL_FIXTURE'
                      for x in (plan.get('grades') or {}).values()) else 'NOT_RUN'),
        'formal_exam_authorized': False,
    }
