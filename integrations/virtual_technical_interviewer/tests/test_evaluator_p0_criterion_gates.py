"""P0 evaluator: contextual replay, semantic admissibility and SQL static guard.

Synthetic fixtures only. Does not call a model, run SQL, write saves or use API keys.
"""
import copy
import hashlib
import json
import unittest
from tia_runtime import native_evaluator as ev
from tia_runtime.evaluator_p0_guards import eligible_aliases, static_sql_signals


def event(actor, kind, ident, text, operation=None):
    return {'actor':actor,'kind':kind,'id':ident,
            'provenance':'LIVE_MODEL' if actor=='interviewer' else 'USER_SAID',
            'payload':{'operation':operation or ('reply' if actor=='interviewer' else kind), 'text':text}}


def plan(events):
    return {'status':'COMPLETE','results':[{'session':{'events':events}}]}


class EvaluatorP0Tests(unittest.TestCase):
    def setUp(self):
        self.events=[
            event('interviewer','reply','q-1','Please give your approach.'),
            event('candidate','clarify','q-2','So firstly we group by country and month.'),
            event('interviewer','reply','q-3','How will you check approval counts?'),
            event('candidate','clarify','q-4','My plan is to use two CTEs and then LEFT JOIN.'),
            event('interviewer','reply','q-5','What steps would verify your query?')]

    def test_full_ordered_interviewer_context_even_for_clarify(self):
        c,r,n=ev._evidence(plan(self.events),0)
        self.assertEqual([x['event_id'] for x in r],['q-1','q-3','q-5'])
        self.assertEqual([x['event_id'] for x in c],['q-2','q-4'])
        self.assertEqual(n,0)

    def test_no_implicit_truncation_of_relevant_turn(self):
        modified=copy.deepcopy(self.events)
        modified[1]['payload']['text']='x'*5000
        with self.assertRaisesRegex(ev.NativeEvaluatorError,'EVALUATOR_CONTEXT_INCOMPLETE'):
            ev._evidence(plan(modified),0)

    def test_user_kind_flip_does_not_hide_interviewer_reply(self):
        a=ev._evidence(plan(self.events),0)[1]
        modified=copy.deepcopy(self.events)
        for e in modified:
            if e['actor']=='candidate':e['kind']='plan'
        b=ev._evidence(plan(modified),0)[1]
        self.assertEqual([r['event_id'] for r in a],[r['event_id'] for r in b])

    def test_clarify_label_alone_cannot_authorize_debugging(self):
        c,r,_=ev._evidence(plan(self.events),0)
        acc={'status':'NOT_VERIFIED','candidate_event_id':None}
        self.assertEqual(eligible_aliases('T04',c,r,acc),[])

    def test_plan_can_support_plan_dimension(self):
        c,r,_=ev._evidence(plan(self.events),0)
        self.assertTrue(eligible_aliases('T03',c,r,{'status':'NOT_VERIFIED'}))

    def test_code_only_not_oral_communication(self):
        sql="SELECT person_name FROM Queue ORDER BY turn DESC LIMIT 1"
        c,r,_=ev._evidence(plan([self.events[0],event('candidate','implement','q-sql',sql)]),0)
        for criterion in ('C01','C02','C03','C04','T04','T05'):
            self.assertEqual(eligible_aliases(criterion,c,r,{'status':'NOT_VERIFIED'}),[],criterion)
        self.assertEqual(eligible_aliases('T02',c,r,{'status':'NOT_VERIFIED'}),['e1'])

    def test_initial_question_not_feedback_integration(self):
        c,r,_=ev._evidence(plan([self.events[0],event('candidate','implement','q-sql','SELECT * FROM Queue')]),0)
        self.assertEqual(eligible_aliases('C05',c,r,{'status':'NOT_VERIFIED'}),[])

    def test_true_feedback_requires_change_and_candidate_preceding(self):
        events=[event('candidate','plan','a','My plan is to join two tables'),
                event('interviewer','reply','b','Your plan has an issue: the join duplicates rows.'),
                event('candidate','plan','c','I revised the join to group before combining.')]
        c,r,_=ev._evidence(plan(events),0)
        self.assertEqual(eligible_aliases('C05',c,r,{'status':'NOT_VERIFIED'}),['e2'])

    def test_correctness_requires_verified_execution(self):
        c,r,_=ev._evidence(plan([self.events[0],event('candidate','implement','q-sql','SELECT 1')]),0)
        self.assertEqual(eligible_aliases('T01',c,r,{'status':'NOT_VERIFIED'}),[])
        self.assertEqual(eligible_aliases('T01',c,r,{'status':'PASSED','candidate_event_id':'q-sql'}),['e1'])

    def test_only_provisional_observation_allowed(self):
        c,r,_=ev._evidence(plan([self.events[0],event('candidate','implement','q-sql','SELECT 1')]),0)
        rubric=ev.compile_evaluator_profile()['rubric']
        criteria=ev._criteria({'rubric':rubric},c,r,{'status':'NOT_VERIFIED','candidate_event_id':None})
        rows=[[x['id'],2,['e1'],'Proposed though not directly observed.'] if x['id'] in ('T02','T04','C01')
              else [x['id'],None,[],'Not observed in current source.'] for x in criteria]
        p={'assessments':rows}
        packet={'candidate_evidence':c,'criteria':criteria,'local_execution':{'status':'NOT_VERIFIED'}}
        out=ev._assessed_dimensions(p,packet)
        for id in ('T04','C01'):
            row=next(x for x in out if x['id']==id)
            self.assertIsNone(row['provisional_points'])
            self.assertEqual(row['admissibility_audit']['gate'],'CRITERION_EVIDENCE_INADMISSIBLE')
        self.assertEqual(next(x for x in out if x['id']=='T02')['anchor_0_to_4'],2)

    def test_forged_alias_still_rejected(self):
        c,r,_=ev._evidence(plan([self.events[0],event('candidate','implement','q-sql','SELECT 1')]),0)
        rubric=ev.compile_evaluator_profile()['rubric']
        criteria=ev._criteria({'rubric':rubric},c,r,{'status':'NOT_VERIFIED'})
        rows=[[x['id'],2,['forged-alias'],'Evidence from text is provided.'] if x['id']=='T02'
              else [x['id'],None,[],'No data supports this item.'] for x in criteria]
        with self.assertRaisesRegex(ev.NativeEvaluatorError,'UNCITED_OR_CROSS_QUESTION'):
            ev._assessed_dimensions({'assessments':rows},{'candidate_evidence':c,'criteria':criteria,'local_execution':{'status':'NOT_VERIFIED'}})

    def test_q3_static_review_is_not_a_test_pass(self):
        sql='''select person_name from (select * from (select *, sum(weight) over(order by turn rows between unbounded preceding and current row) as running from Queue) where running <= 1000) order by turn desc limit 1;'''
        c,r,_=ev._evidence(plan([self.events[0],event('candidate','implement','q-sql',sql)]),0)
        out=static_sql_signals({'title':'Last Person to Fit in the Bus'},c)
        self.assertTrue(out['structural_match_all'])
        self.assertEqual(out['correctness'],'NOT_VERIFIED')
        self.assertEqual(out['execution'],'NOT_RUN')
        self.assertIn('PostgreSQL 16+',out['dialect_note'])

    def test_wrong_sql_does_not_pass_structural_match(self):
        c,r,_=ev._evidence(plan([self.events[0],event('candidate','implement','q-sql','SELECT * FROM Queue')]),0)
        out=static_sql_signals({'title':'Last Person to Fit in the Bus'},c)
        self.assertFalse(out['structural_match_all'])

if __name__=='__main__':unittest.main()
