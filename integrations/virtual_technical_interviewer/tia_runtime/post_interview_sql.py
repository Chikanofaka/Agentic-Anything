"""Versioned retrospective SQL checks; frozen interviews are never rewritten.

A candidate selects a reviewed synthetic suite that matches their source task.
Native consent binds the source, submitted SQL, and every expected output. No
model chooses results and no provider is called. These finite cases are not
exhaustive correctness proofs or official hidden tests.
"""
import copy
import hashlib
import json
import re

from .sql_accuracy import validate_fixture, grade_fixture, AccuracyError
from .grading_binding import find_approved_pg_config, GradingBindingError

SCHEMA = 'tia-post-interview-sql/v1'
SHA = re.compile(r'[0-9a-f]{64}\Z')
SUITES = {
    'delivery_first_orders': {'title': 'Immediate first deliveries',
        'assumptions': 'Delivery has one earliest order per customer. Immediate means order_date equals customer_pref_delivery_date. Return immediate_percentage rounded to two decimal places. Empty customer sets are not covered.',
        'columns': [('delivery_id','INTEGER'),('customer_id','INTEGER'),('order_date','DATE'),('customer_pref_delivery_date','DATE')],
        'table':'Delivery', 'output':['immediate_percentage'],
        'cases':[
            ('first-order-not-any-order', [[1,1,'2024-01-01','2024-01-02'],[2,1,'2024-01-03','2024-01-03'],[3,2,'2024-01-02','2024-01-02'],[4,2,'2024-01-06','2024-01-07']], [['50.00']]),
            ('rounding-and-multiple-orders', [[1,1,'2024-01-01','2024-01-01'],[2,2,'2024-01-01','2024-01-02'],[3,3,'2024-01-02','2024-01-03'],[4,3,'2024-01-03','2024-01-03']], [['33.33']]),
            ('no-immediate-first-orders', [[1,1,'2024-01-01','2024-01-02'],[2,2,'2024-01-02','2024-01-03']], [['0.00']])]},
    'monthly_transactions': {'title':'Monthly transaction aggregates',
        'assumptions':'Transactions has state approved or declined and groups by calendar year-month and country, including NULL country. Count/sum all transactions and separately state=approved; missing approved groups produce zero. Return month,country,trans_count,approved_count,trans_total_amount,approved_total_amount. Row order is ignored.',
        'columns':[('id','INTEGER'),('country','TEXT'),('state','TEXT'),('amount','INTEGER'),('trans_date','DATE')],
        'table':'Transactions', 'output':['month','country','trans_count','approved_count','trans_total_amount','approved_total_amount'],
        'cases':[
            ('approved-declined-and-missing-group',[[1,'US','approved',100,'2024-01-02'],[2,'US','declined',50,'2024-01-20'],[3,'CA','declined',70,'2024-01-12']], [['2024-01','US',2,1,150,100],['2024-01','CA',1,0,70,0]]),
            ('null-country-and-year-boundary',[[1,None,'approved',30,'2023-12-31'],[2,None,'declined',20,'2023-12-01'],[3,'US','approved',40,'2024-01-01'],[4,'US','declined',10,'2023-01-01']], [['2023-12',None,2,1,50,30],['2024-01','US',1,1,40,40],['2023-01','US',1,0,10,0]]),
            ('duplicate-amounts-and-zero',[[1,'US','approved',50,'2024-02-01'],[2,'US','approved',50,'2024-02-02'],[3,'US','declined',0,'2024-02-03']], [['2024-02','US',3,2,100,100]])]},
    'bus_last_person': {'title':'Last person within a 1000 kg bus limit',
        'assumptions':'Queue has unique turn, positive weight, and first person fits. Board in turn order and stop before the first cumulative weight exceeding 1000. Return person_name; physical insertion order is irrelevant.',
        'columns':[('person_id','INTEGER'),('person_name','TEXT'),('weight','INTEGER'),('turn','INTEGER')],
        'table':'Queue','output':['person_name'],
        'cases':[
            ('exact-capacity-and-unsorted-input',[[3,'C',1,3],[1,'A',400,1],[2,'B',600,2]], [['B']]),
            ('overflow-stops-boarding',[[1,'A',800,1],[2,'B',250,2],[3,'C',10,3]], [['A']]),
            ('all-fit',[[2,'B',200,2],[1,'A',100,1],[3,'C',300,3]], [['C']])]}}

class PostSQLError(ValueError):
    def __init__(self, code): self.code=code; super().__init__(code)

def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def sha(value): return hashlib.sha256(canonical(value).encode()).hexdigest()
def text_sha(value): return hashlib.sha256(value.encode('utf-8')).hexdigest()

def source(plan,index):
    if type(index) is not int or index not in range(3) or type(plan) is not dict or plan.get('status') not in ('COMPLETE','TIMED_OUT','CLOCK_INTEGRITY_HOLD') or len(plan.get('results',[]))!=3:
        raise PostSQLError('POST_SQL_REQUIRES_CLOSED_INTERVIEW')
    question=plan['questions'][index]; record=plan['results'][index]
    if question.get('environment')!='POSTGRESQL': raise PostSQLError('POST_SQL_POSTGRESQL_ONLY')
    events=((record.get('session') or {}).get('events') or [])
    choices=[e for e in events if e.get('actor')=='candidate' and e.get('kind')=='implement']
    if not choices: raise PostSQLError('POST_SQL_NO_SUBMISSION')
    candidate=choices[-1]; code=candidate['payload']['text']
    if type(code) is not str or len(code.encode())>8192: raise PostSQLError('POST_SQL_INVALID_SUBMISSION')
    return {'question_index':index,'question_sha256':question['content_sha256'],
            'record_sha256':sha({'question':question,'record':record}),
            'candidate_event_id':candidate['id'],'candidate_sql_sha256':text_sha(code)},code

def fixtures(suite_id, question_sha256):
    if suite_id not in SUITES or type(question_sha256) is not str or not SHA.fullmatch(question_sha256): raise PostSQLError('POST_SQL_INVALID_SUITE')
    suite=SUITES[suite_id]; out=[]
    for label,rows,expected in suite['cases']:
        fixture={'schema':'tia-postgres-fixture/v1','fixture_id':suite_id+'-'+label,
            'question_sha256':question_sha256,'environment':'POSTGRESQL',
            'tables':[{'name':suite['table'],'columns':[{'name':n,'type':t} for n,t in suite['columns']],'rows':rows}],
            'expected':{'columns':suite['output'],'rows':expected,'order_sensitive':False}}
        blob=canonical(fixture).encode(); _, digest=validate_fixture(blob)
        out.append({'fixture':fixture,'fixture_sha256':digest,'label':label})
    return out

def review(plan,index,suite_id):
    binding,_=source(plan,index)
    if suite_id not in SUITES: raise PostSQLError('POST_SQL_INVALID_SUITE')
    suite=SUITES[suite_id]; cases=fixtures(suite_id,binding['question_sha256'])
    out={'schema':SCHEMA,**binding,'suite_id':suite_id,'title':suite['title'],
         'assumptions':suite['assumptions'],'cases':cases,'case_count':len(cases),
         'suite_sha256':sha(cases),'official_hidden_tests':False,
         'status':'AWAITING_NATIVE_HUMAN_APPROVAL'}
    out['review_sha256']=sha(out)
    return out

def prepare(plan, reviewed, request_id, generation):
    if type(reviewed) is not dict or review(plan,reviewed['question_index'],reviewed['suite_id'])!=reviewed: raise PostSQLError('POST_SQL_STALE_REVIEW')
    if any(type(v) is not str or re.fullmatch(r'[A-Za-z0-9_-]{1,80}',v) is None for v in (request_id,generation)): raise PostSQLError('POST_SQL_INVALID_TOKEN')
    binding,code=source(plan,reviewed['question_index'])
    pending={'request_id':request_id,'generation':generation,'review_sha256':reviewed['review_sha256'],**binding,'suite_id':reviewed['suite_id'],'suite_sha256':reviewed['suite_sha256']}
    return pending,{'schema':SCHEMA,'pending':pending,'candidate_sql':code,'cases':reviewed['cases']}

def validate_pending(pending):
    expected={'request_id','generation','review_sha256','question_index','question_sha256',
              'record_sha256','candidate_event_id','candidate_sql_sha256','suite_id','suite_sha256'}
    if type(pending) is not dict or set(pending)!=expected:
        raise PostSQLError('POST_SQL_INVALID_BINDING')
    if type(pending['question_index']) is not int or pending['question_index'] not in range(3):
        raise PostSQLError('POST_SQL_INVALID_BINDING')
    for key in ('review_sha256','question_sha256','record_sha256','candidate_sql_sha256','suite_sha256'):
        if type(pending[key]) is not str or SHA.fullmatch(pending[key]) is None:
            raise PostSQLError('POST_SQL_INVALID_BINDING')
    for key in ('request_id','generation'):
        if type(pending[key]) is not str or re.fullmatch(r'[A-Za-z0-9_-]{1,80}',pending[key]) is None:
            raise PostSQLError('POST_SQL_INVALID_BINDING')
    event=pending['candidate_event_id']
    if type(event) is not str or not 1 <= len(event) <= 256 or any(ord(c)<32 for c in event):
        raise PostSQLError('POST_SQL_INVALID_BINDING')
    if type(pending['suite_id']) is not str or pending['suite_id'] not in SUITES:
        raise PostSQLError('POST_SQL_INVALID_BINDING')

def execute(packet, *, runner=grade_fixture, pg_config=None):
    if type(packet) is not dict or set(packet)!={'schema','pending','candidate_sql','cases'} or packet['schema']!=SCHEMA: raise PostSQLError('POST_SQL_INVALID_REQUEST')
    p=packet['pending']; validate_pending(p)
    if type(packet['candidate_sql']) is not str or not 1 <= len(packet['candidate_sql'].encode()) <= 8192:
        raise PostSQLError('POST_SQL_INVALID_SUBMISSION')
    cases=fixtures(p['suite_id'],p['question_sha256'])
    if packet['cases']!=cases or sha(cases)!=p['suite_sha256'] or text_sha(packet['candidate_sql'])!=p['candidate_sql_sha256']: raise PostSQLError('POST_SQL_BINDING_MISMATCH')
    outcomes=[]
    for case in cases:
        try:
            config=pg_config or find_approved_pg_config()
            result=runner(canonical(case['fixture']).encode(),packet['candidate_sql'],case['fixture_sha256'],pg_config=config,private_query=True)
            row=result['result']; status=row['status']
            outcomes.append({'fixture_sha256':case['fixture_sha256'],'label':case['label'],'status':status,'reason':row.get('reason',row.get('error_code',''))})
        except (AccuracyError,GradingBindingError) as e:
            outcomes.append({'fixture_sha256':case['fixture_sha256'],'label':case['label'],'status':'NOT_VERIFIED','reason':e.code})
    result={'schema':SCHEMA,'pending':p,'cases':outcomes,'source':'EPHEMERAL_POSTGRESQL_LOCAL','official_hidden_tests':False}
    result['sha256']=sha(result)
    return result

def commit(plan,pending,result):
    validate_pending(pending)
    if type(pending) is not dict or type(result) is not dict or set(result)!={'schema','pending','cases','source','official_hidden_tests','sha256'}: raise PostSQLError('POST_SQL_INVALID_RESULT')
    if result['schema']!=SCHEMA or result['pending']!=pending or result['sha256']!=sha({k:v for k,v in result.items() if k!='sha256'}) or result['source']!='EPHEMERAL_POSTGRESQL_LOCAL' or result['official_hidden_tests'] is not False: raise PostSQLError('POST_SQL_BINDING_MISMATCH')
    binding,_=source(plan,pending['question_index'])
    if any(pending.get(k)!=v for k,v in binding.items()): raise PostSQLError('POST_SQL_STALE_RESULT')
    expected=fixtures(pending['suite_id'],pending['question_sha256'])
    if sha(expected)!=pending['suite_sha256'] or type(result['cases']) is not list or len(result['cases'])!=len(expected): raise PostSQLError('POST_SQL_CASE_MISMATCH')
    for case,wanted in zip(result['cases'],expected):
        if type(case) is not dict or set(case)!={'fixture_sha256','label','status','reason'} or case['fixture_sha256']!=wanted['fixture_sha256'] or case['label']!=wanted['label'] or case['status'] not in ('PASSED','FAILED','EXECUTION_ERROR','NOT_VERIFIED') or type(case['reason']) is not str or not re.fullmatch(r'[A-Z_]{0,80}',case['reason']): raise PostSQLError('POST_SQL_INVALID_CASE_RESULT')
    out=copy.deepcopy(result); statuses=[x['status'] for x in out['cases']]
    out['status']=('NOT_VERIFIED' if 'NOT_VERIFIED' in statuses else 'EXECUTION_ERROR' if 'EXECUTION_ERROR' in statuses else 'FAILED' if 'FAILED' in statuses else 'PASSED')
    out['passed']=statuses.count('PASSED'); out['total']=len(statuses)
    out['execution_time']='AFTER_INTERVIEW'; out['question_index']=pending['question_index']
    return out

def evaluation_plan(plan, results):
    """A separate derived evaluation source. Original timing/transcripts stay intact."""
    out=copy.deepcopy(plan)
    for index,observation in results.items():
        verified=commit(plan,observation['pending'],{k:v for k,v in observation.items() if k in ('schema','pending','cases','source','official_hidden_tests','sha256')})
        if verified['status']=='NOT_VERIFIED': continue
        p=verified['pending']; result=out['results'][int(index)]
        result['sql_accuracy']={'schema':'tia-post-interview-sql-accuracy/v1','source':'EPHEMERAL_POSTGRESQL_LOCAL',
            'correctness':'VERIFIED_LOCAL_FIXTURE','approval_kind':'NATIVE_HUMAN_CONFIRMATION','official_hidden_tests':False,
            'question_sha256':p['question_sha256'],'candidate_event_id':p['candidate_event_id'],'candidate_sql_sha256':p['candidate_sql_sha256'],
            'fixture_sha256':p['suite_sha256'],'total_approved_fixtures':verified['total'],'passed_fixtures':verified['passed'],
            'result':{'status':verified['status']},'post_interview_observation':verified}
    return out
