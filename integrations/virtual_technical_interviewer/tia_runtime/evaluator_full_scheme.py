"""Read-only, deterministic three-question Evaluator scheme for Technical Interview Lab.

This module never calls an AI provider, executes SQL or approves rubric weights.
Its output is a decision SUPPORT summary of the existing frozen v1 report,
not a credential, final score, or replay of private interview transcript.
"""
from __future__ import annotations

import copy
import hashlib
import json

SCHEMA = 'tia-evaluator-full-scheme/v1'
IDS = ('T01','T02','T03','T04','T05','C01','C02','C03','C04','C05','C06')
AXES = {'technical': IDS[:5], 'communication': IDS[5:]}
MAX = {'technical': 60, 'communication': 40}
LEGACY = 'LEGACY_CONTEXT_REVIEW_REQUIRED'

class SchemeError(ValueError):
    pass


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def _check_question(q, index):
    if not isinstance(q, dict) or q.get('index') != index or not isinstance(q.get('dimensions'), list):
        raise SchemeError('QUESTION_ORDER_INVALID')
    dimensions = q['dimensions']
    if len(dimensions) != len(IDS) or [d.get('id') for d in dimensions] != list(IDS):
        raise SchemeError('CRITERION_MATRIX_INVALID')
    for d in dimensions:
        points, weight, anchor = d.get('provisional_points'), d.get('proposed_max_points'), d.get('anchor_0_to_4')
        if (type(weight) not in (int,float) or weight <= 0 or weight > 100 or
                d.get('axis') != ('technical' if d['id'].startswith('T') else 'communication')):
            raise SchemeError('CRITERION_WEIGHT_INVALID')
        if anchor is not None:
            if (type(anchor) is not int or not 0 <= anchor <= 3 or
                    type(points) not in (int,float) or abs(points-weight*anchor/4)>1e-7 or
                    d.get('status') != 'MODEL_PROPOSED'):
                raise SchemeError('CRITERION_POINTS_INVALID')
        elif points is not None:
            raise SchemeError('UNOBSERVED_POINTS_INVALID')
    for axis, group in AXES.items():
        if sum(d['proposed_max_points'] for d in dimensions if d['id'] in group) != MAX[axis]:
            raise SchemeError('RUBRIC_TOTAL_INVALID')


def compile_full_scheme(report):
    """Aggregate one validated Host report, never rewriting its inputs or missing scores."""
    if not isinstance(report, dict) or report.get('schema') != 'tia-evaluator-report/v1':
        raise SchemeError('REPORT_SCHEMA_INVALID')
    questions = report.get('questions')
    if not isinstance(questions, list) or len(questions) != 3:
        raise SchemeError('THREE_QUESTION_CONTRACT_REQUIRED')
    if (report.get('proposed_weight_policy', {}).get('technical') != 60 or
            report.get('proposed_weight_policy', {}).get('communication') != 40 or
            report.get('proposed_weight_policy', {}).get('status') != 'UNCALIBRATED_HYPOTHESIS'):
        raise SchemeError('RUBRIC_AUTHORITY_INVALID')

    per_q = []
    aggregated = {a: {'observed_provisional_points': 0, 'covered_weight': 0,
                      'maximum_weight': MAX[a]*3, 'observed_dimensions': 0,
                      'possible_dimensions': len(AXES[a])*3} for a in AXES}
    evaluated_count = legacy_count = rejected_count = 0
    action_candidates = []
    for index,q in enumerate(questions):
        _check_question(q, index)
        assessment = q.get('assessment')
        historical = isinstance(assessment, dict) and assessment.get('status') == LEGACY
        current = isinstance(assessment, dict) and assessment.get('status') == 'PENDING_HUMAN_REVIEW'
        if assessment and not (historical or current):
            raise SchemeError('ASSESSMENT_STATUS_INVALID')
        if historical: legacy_count += 1
        if current: evaluated_count += 1
        status = LEGACY if historical else ('PENDING_HUMAN_REVIEW' if current else 'NOT_EVALUATED')
        rows = []
        for d in q['dimensions']:
            gate = (d.get('admissibility_audit') or {}).get('gate')
            blocked = bool(current and (d.get('admissibility_audit') or {}).get('disallowed_proposal_anchor') is not None)
            if blocked: rejected_count += 1
            candidate_refs = [r.get('event_id') for r in (d.get('evidence') or [])
                              if isinstance(r,dict) and isinstance(r.get('event_id'),str)]
            # Existing scores from pre-P0 input selector remain archived, not included
            # in current-version aggregates or promoted to verified observations.
            valid = current and d.get('status') == 'MODEL_PROPOSED' and d.get('anchor_0_to_4') is not None
            rows.append({'id': d['id'], 'title': d.get('title',''), 'axis':d['axis'],
                         'max_points':d['proposed_max_points'], 'status': d.get('status'),
                         'eligible_provisional_points':d['provisional_points'] if valid else None,
                         'anchor':d['anchor_0_to_4'] if valid else None,
                         'citations':candidate_refs if valid else [],
                         'admissibility':gate or ('LEGACY_UNVERIFIED' if historical else 'NOT_AVAILABLE'),
                         'blocked':blocked})
            if valid and d['anchor_0_to_4'] <= 1:
                action_candidates.append({'question_index': index, 'criterion_id':d['id'],
                    'kind':'PRACTICE_EVIDENCED_GAP', 'evidence_event_ids':candidate_refs,
                    'reason':'Low model-proposed anchor; not an independently verified performance deficit.'})
        summary = {}
        for axis in AXES:
            eligible = [d for d in rows if d['axis']==axis and d['eligible_provisional_points'] is not None]
            pts = sum(d['eligible_provisional_points'] for d in eligible)
            weight = sum(d['max_points'] for d in eligible)
            summary[axis] = {'observed_provisional_points':round(pts,4) if eligible else None,
                             'covered_weight':weight, 'maximum_weight':MAX[axis],
                             'unobserved_weight':MAX[axis]-weight,
                             'observed_dimensions':len(eligible),'total_dimensions':len(AXES[axis]),
                             'coverage_percent':round(weight/MAX[axis]*100,2),
                             'final_score':'NOT_SCORED'}
            aggregated[axis]['observed_provisional_points'] += pts
            aggregated[axis]['covered_weight'] += weight
            aggregated[axis]['observed_dimensions'] += len(eligible)
        accuracy = (q.get('raw_metrics') or {}).get('accuracy') or {}
        sql = copy.deepcopy(q.get('static_sql_review') or {})
        # Do not reflect model text or SQL itself in the aggregate. Refer by IDs/hashes.
        sql_status = {'local_execution': accuracy.get('status','NOT_VERIFIED'),
            'static_review':sql.get('status','UNAVAILABLE'),
            'static_pattern_match':sql.get('structural_match_all') if sql.get('status')=='STATIC_REVIEW_ONLY' else None,
            'dialect_note':sql.get('dialect_note',''), 'official_hidden_test_result':'NOT_AVAILABLE',
            'correctness_grade': 'NOT_SCORED'}
        per_q.append({'index':index,'title':q.get('title',''), 'evaluation_status':status,
                      'technical':summary['technical'],'communication':summary['communication'],
                      'dimensions':rows,'sql':sql_status,
                      'blocked_criterion_ids':[r['id'] for r in rows if r['blocked']],
                      'required_next_action':('NONE_NO_AUTOMATIC_REEVALUATION' if historical else
                         'EVALUATE_WITH_SEPARATE_CONSENT' if not current else 'SEMANTIC_REVIEW_REQUIRED')})
    for axis,tot in aggregated.items():
        tot['observed_provisional_points'] = round(tot['observed_provisional_points'],4) if tot['observed_dimensions'] else None
        tot['unobserved_weight'] = tot['maximum_weight']-tot['covered_weight']
        tot['coverage_percent']=round(tot['covered_weight']/tot['maximum_weight']*100,2)
        tot['grade']='NOT_SCORED'

    out = {'schema':SCHEMA, 'source_rubric_version':report.get('rubric_version'),
           'prompt_sha256':report.get('prompt_sha256'), 'status':'PROVISIONAL_HUMAN_REVIEW_REQUIRED' if evaluated_count else 'NO_CURRENT_SEMANTIC_REVIEW',
           'formal_authority':'UNAPPROVED_SUBWEIGHTS_UNCALIBRATED',
           'final_technical_score':'NOT_SCORED','final_communication_score':'NOT_SCORED',
           'final_overall_score':'NOT_SCORED',
           'evaluations_current':evaluated_count, 'evaluations_legacy':legacy_count,
           'questions_total':3,'blocked_proposal_dimensions':rejected_count,
           'technical':aggregated['technical'],'communication':aggregated['communication'],
           'questions':per_q, 'drill_candidates':action_candidates[:10],
           'release_blockers':['HUMAN_SEMANTIC_REVIEW_NOT_CERTIFIED',
                'SUBWEIGHTS_NOT_APPROVED','NO_AUTHORIZED_COMPREHENSIVE_SQL_FIXTURE_CERTIFICATION'],
           'limitations':['Coverage is measured against all three question weights, not an earned score.',
                'Unobserved and unevaluated criteria are unknown, not zero.',
                'A static SQL pattern match does not establish correctness or execute PostgreSQL.',
                'This aggregate makes no new model calls, provider charges or approval decisions.',
                'Legacy proposals remain visible but are excluded from current evidence totals.']}
    out['sha256']=_sha(out)
    return out
