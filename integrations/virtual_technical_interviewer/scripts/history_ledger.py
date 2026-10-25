#!/usr/bin/env python3
"""Private, content-minimal interview history. No model or SQL execution.

Only hashes and bounded numeric metrics from explicitly exported local receipts are
recorded. The original transcript stays in the user's export location.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

SCHEMA = 'tia-evaluator-private-history/v1'
ENTRY_FIELDS = ('receipt_sha256','session_status','verified_local_questions','technical_coverage_weight',
                'communication_coverage_weight','blocked_proposals','practice_attempts','formally_scored')
MAX_BYTES = 20_000_000

def validate_export(path):
    if path.is_symlink() or not path.is_file(): raise ValueError('EXPORT_FILE_UNSAFE')
    if path.stat().st_size == 0 or path.stat().st_size > MAX_BYTES:raise ValueError('EXPORT_SIZE_INVALID')
    data = path.read_bytes()
    obj = json.loads(data)
    if type(obj) is not dict or obj.get('schema') != 'tia-tutorial-export/v1':
        raise ValueError('EXPORT_SCHEMA_INVALID')
    rehearsal=obj.get('rehearsal')
    if type(rehearsal) is not dict or rehearsal.get('status') not in ('COMPLETE','TIMED_OUT','CLOCK_INTEGRITY_HOLD'):
        raise ValueError('NO_CLOSED_REHEARSAL')
    if not isinstance(rehearsal.get('results'),list) or len(rehearsal['results'])!=3:
        raise ValueError('THREE_QUESTION_RECORD_REQUIRED')
    scheme=(obj.get('evaluator_report') or {}).get('full_scheme') or {}
    if scheme and (scheme.get('schema')!='tia-evaluator-full-scheme/v1' or
                   scheme.get('final_overall_score')!='NOT_SCORED'):
        raise ValueError('UNTRUSTED_FORMAL_SCORE_CLAIM')
    acc=(obj.get('evidence_scorecard') or {}).get('summary') or {}
    reported=acc.get('latest_sql_locally_verified_questions',0)
    if type(reported) is not int or not 0<=reported<=3:raise ValueError('EXECUTION_COUNTER_INVALID')
    tech=(scheme.get('technical') or {}).get('covered_weight',0)
    comm=(scheme.get('communication') or {}).get('covered_weight',0)
    blocked=scheme.get('blocked_proposal_dimensions',0)
    progress=(obj.get('smart_progress_summary') or {}).get('recorded_attempts',0)
    for name,value,maximum in [('technical',tech,180),('communication',comm,120),('blocked',blocked,33),('progress',progress,100000)]:
        if type(value) is not int or not 0<=value<=maximum:raise ValueError('INVALID_COUNTER_'+name)
    return {'receipt_sha256':hashlib.sha256(data).hexdigest(),
            'session_status':rehearsal['status'], 'verified_local_questions':reported,
            'technical_coverage_weight':tech,'communication_coverage_weight':comm,
            'blocked_proposals':blocked,'practice_attempts':progress, 'formally_scored':False}

def read_ledger(path):
    if not path.exists():return {'schema':SCHEMA,'records':[]}
    if path.is_symlink() or path.stat().st_size>2_000_000:raise ValueError('LEDGER_UNSAFE')
    content=json.loads(path.read_text(encoding='utf-8'))
    if type(content) is not dict or content.get('schema')!=SCHEMA or type(content.get('records')) is not list or len(content['records'])>5000:
        raise ValueError('LEDGER_INVALID')
    if any(type(r) is not dict or set(r)!=set(ENTRY_FIELDS) for r in content['records']):raise ValueError('LEDGER_ENTRY_INVALID')
    return content

def write_ledger(path,ledger):
    parent=path.parent
    if parent.is_symlink():raise ValueError('LEDGER_PARENT_UNSAFE')
    parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    if os.name=='posix':os.chmod(parent,0o700)
    fd,temp=tempfile.mkstemp(dir=parent,prefix='.tia-history-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as output:
            json.dump(ledger,output,sort_keys=True,indent=2)
            output.flush();os.fsync(output.fileno())
        os.chmod(temp,0o600)
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def execute(args):
    destination=Path(args.ledger).expanduser() if args.ledger else (Path.home()/'Library/Application Support/Technical Interview Lab/private-history.json')
    if args.record:
        entry=validate_export(Path(args.record).expanduser())
        ledger=read_ledger(destination)
        if any(x['receipt_sha256']==entry['receipt_sha256'] for x in ledger['records']):
            print('TIA_HISTORY=ALREADY_RECORDED_NO_WRITE')
        else:
            if len(ledger['records'])>=5000:raise ValueError('HISTORY_CAP_REACHED')
            ledger['records'].append(entry);write_ledger(destination,ledger)
            print('TIA_HISTORY=RECORDED_PRIVATE_SUMMARY_ONLY')
    else:ledger=read_ledger(destination)
    print('TIA_HISTORY_RECORDS='+str(len(ledger['records'])))
    for i,entry in enumerate(ledger['records'][-10:],max(1,len(ledger['records'])-9)):
        print(f'RUN={i} FINGERPRINT={entry["receipt_sha256"][:12]} '
              f'VERIFIED_LOCAL={entry["verified_local_questions"]}/3 '
              f'EVIDENCE_COVERAGE_T={entry["technical_coverage_weight"]}/180 '
              f'C={entry["communication_coverage_weight"]}/120 '
              f'SELF_REPORTED_ACTIVITIES={entry["practice_attempts"]} '
              'FORMAL_SCORE=NOT_SCORED')
    if len(ledger['records'])>=2:
        old,new=ledger['records'][-2:]
        print('COVERAGE_DELTA_ONLY_T='+str(new['technical_coverage_weight']-old['technical_coverage_weight']))
        print('COVERAGE_DELTA_ONLY_C='+str(new['communication_coverage_weight']-old['communication_coverage_weight']))
        print('NOTICE=COVERAGE_CHANGE_IS_NOT_CERTIFIED_SKILL_IMPROVEMENT')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--record',help='Existing explicitly exported local session receipt JSON')
    group.add_argument('--list',action='store_true')
    parser.add_argument('--ledger',help='Override private ledger destination (for tests)')
    args=parser.parse_args()
    try:execute(args)
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
        print('TIA_HISTORY=HOLD REASON='+str(e));sys.exit(2)
