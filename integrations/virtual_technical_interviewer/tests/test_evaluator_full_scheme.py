"""Offline deterministic evaluation scheme acceptance tests. No private interview data."""
import copy
import hashlib
import json
import unittest
from tia_runtime.evaluator_full_scheme import compile_full_scheme, SchemeError

WEIGHTS={'T01':24,'T02':13,'T03':10,'T04':9,'T05':4,'C01':6,'C02':7,'C03':7,'C04':9,'C05':7,'C06':4}


def report_with_assessments(indices=(), legacy=(), proposed=None, blocked=()):
    proposed=proposed or {}
    questions=[]
    for index in range(3):
        dims=[]
        for name,weight in WEIGHTS.items():
            anchor=proposed.get((index,name)) if index in indices or index in legacy else None
            applied = anchor is not None and (index,name) not in blocked
            dims.append({'id':name,'axis':'technical' if name[0]=='T' else 'communication',
                'title':name,'proposed_max_points':weight,'status':'MODEL_PROPOSED' if applied else 'NOT_OBSERVED',
                'anchor_0_to_4':anchor if applied else None,
                'provisional_points':weight*anchor/4 if applied else None,
                'evidence':[{'event_id':'synthetic-event-q'+str(index)}] if applied else [],
                'admissibility_audit':{'gate':'ELIGIBLE_FOR_HUMAN_SEMANTIC_REVIEW' if applied else 'CRITERION_EVIDENCE_INADMISSIBLE',
                    'disallowed_proposal_anchor':anchor if (index,name) in blocked else None}})
        questions.append({'index':index,'title':'Question '+str(index+1),'dimensions':dims,
            'assessment':{'status':'LEGACY_CONTEXT_REVIEW_REQUIRED' if index in legacy else 'PENDING_HUMAN_REVIEW'} if index in (*indices,*legacy) else None,
            'raw_metrics':{'accuracy':{'status':'NOT_VERIFIED'}},
            'static_sql_review':{'status':'STATIC_REVIEW_ONLY','structural_match_all':True,
               'dialect_note':'Static structure only; no engine executed.'}})
    return {'schema':'tia-evaluator-report/v1','questions':questions,
        'proposed_weight_policy':{'technical':60,'communication':40,'status':'UNCALIBRATED_HYPOTHESIS'},
        'rubric_version':'tia-60-40-owner-hypothesis-v0.3','prompt_sha256':'0'*64}

class FullSchemeTests(unittest.TestCase):
    def test_empty_has_no_zero_or_fake_grade(self):
        s=compile_full_scheme(report_with_assessments())
        self.assertIsNone(s['technical']['observed_provisional_points'])
        self.assertEqual(s['technical']['maximum_weight'],180)
        self.assertEqual(s['communication']['maximum_weight'],120)
        self.assertEqual(s['status'],'NO_CURRENT_SEMANTIC_REVIEW')
        self.assertEqual(s['final_overall_score'],'NOT_SCORED')

    def test_three_question_complete_matrix(self):
        s=compile_full_scheme(report_with_assessments(indices=(0,1,2)))
        self.assertEqual(len(s['questions']),3)
        self.assertTrue(all(len(q['dimensions'])==11 for q in s['questions']))

    def test_observed_partial_points_not_normalized(self):
        s=compile_full_scheme(report_with_assessments(indices=(0,),proposed={(0,'T02'):2,(0,'C02'):3}))
        self.assertEqual(s['technical']['observed_provisional_points'],6.5)
        self.assertEqual(s['technical']['covered_weight'],13)
        self.assertEqual(s['technical']['unobserved_weight'],167)
        self.assertEqual(s['communication']['observed_provisional_points'],5.25)
        self.assertEqual(s['communication']['covered_weight'],7)

    def test_zero_is_observed_not_missing(self):
        s=compile_full_scheme(report_with_assessments(indices=(0,),proposed={(0,'T02'):0}))
        self.assertEqual(s['technical']['observed_provisional_points'],0)
        self.assertEqual(s['technical']['covered_weight'],13)

    def test_blocked_anchor_never_awarded(self):
        s=compile_full_scheme(report_with_assessments(indices=(2,),proposed={(2,'C01'):2},blocked={(2,'C01')}))
        self.assertEqual(s['blocked_proposal_dimensions'],1)
        self.assertIsNone(s['questions'][2]['communication']['observed_provisional_points'])
        self.assertIn('C01',s['questions'][2]['blocked_criterion_ids'])

    def test_legacy_not_promoted_or_mutated(self):
        r=report_with_assessments(legacy=(0,),proposed={(0,'T02'):3})
        original=copy.deepcopy(r)
        s=compile_full_scheme(r)
        self.assertEqual(s['evaluations_legacy'],1)
        self.assertIsNone(s['technical']['observed_provisional_points'])
        self.assertEqual(r,original)

    def test_sql_structural_match_stays_unverified(self):
        s=compile_full_scheme(report_with_assessments(indices=(2,),proposed={(2,'T02'):2}))
        q=s['questions'][2]
        self.assertTrue(q['sql']['static_pattern_match'])
        self.assertEqual(q['sql']['local_execution'],'NOT_VERIFIED')
        self.assertEqual(q['sql']['correctness_grade'],'NOT_SCORED')

    def test_drills_only_from_observed_low_anchor(self):
        s=compile_full_scheme(report_with_assessments(indices=(0,),proposed={(0,'T02'):1,(0,'T03'):3}))
        self.assertEqual([x['criterion_id'] for x in s['drill_candidates']],['T02'])

    def test_refuses_12d_rubric(self):
        r=report_with_assessments()
        r['questions'][0]['dimensions'].append({'id':'P01'})
        with self.assertRaisesRegex(SchemeError,'CRITERION_MATRIX_INVALID'):compile_full_scheme(r)

    def test_refuses_wrong_weight(self):
        r=report_with_assessments();r['questions'][2]['dimensions'][0]['proposed_max_points']=25
        with self.assertRaisesRegex(SchemeError,'RUBRIC_TOTAL_INVALID'):compile_full_scheme(r)

    def test_refuses_fake_points(self):
        r=report_with_assessments(indices=(0,),proposed={(0,'T02'):2})
        r['questions'][0]['dimensions'][1]['provisional_points']=99
        with self.assertRaisesRegex(SchemeError,'CRITERION_POINTS_INVALID'):compile_full_scheme(r)

    def test_refuses_approved_scoring_claim(self):
        r=report_with_assessments();r['proposed_weight_policy']['status']='APPROVED'
        with self.assertRaisesRegex(SchemeError,'RUBRIC_AUTHORITY_INVALID'):compile_full_scheme(r)

    def test_stable_deterministic_receipt(self):
        r=report_with_assessments(indices=(2,),proposed={(2,'T02'):2})
        a,b=compile_full_scheme(r),compile_full_scheme(copy.deepcopy(r))
        self.assertEqual(a,b)
        self.assertEqual(len(a['sha256']),64)

if __name__=='__main__':unittest.main(verbosity=2)
