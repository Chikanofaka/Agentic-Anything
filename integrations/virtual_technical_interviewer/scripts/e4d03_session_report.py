#!/usr/bin/env python3
"""TIA E4D-03: private, source-preserving, full-session evaluator status report.

Reads an existing local signed-by-checksum (not cryptographically authenticated)
TIA journal, replays it ONLY in a copied private scratch directory through the
installed Host, and creates a static HTML & JSON session-status artifact.

No model calls, no grading, no original save mutation, no integration with live App.
This is a standalone, real local report; full product integration is separately gated.
"""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import html
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any

EXPECTED_SAVE = 'tutorial-v1.json'
VALID_CODES = ('T01','T02','T03','T04','T05','C01','C02','C03','C04','C05','C06')
EXPERIMENTAL_CODES = ('T1','T2','T3','T4','C1','C2','C3','C4','P1','P2','P3','P4')
MAX_SAVE = 2 * 1024 * 1024

class ReportError(ValueError):
    pass


def _strict_json(raw: bytes):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out: raise ReportError('DUPLICATE_JSON_KEY')
            out[k]=v
        return out
    def reject(_): raise ReportError('NONFINITE_JSON_NUMBER')
    try: return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=reject)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ReportError('INVALID_JSON') from exc


def _canon_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('utf-8')).hexdigest()


def read_save_bytes(path: Path):
    """Open leaf with O_NOFOLLOW and validate complete save digest; no writes."""
    if path.is_symlink(): raise ReportError('SYMLINK_SAVE_REFUSED')
    fd=None
    try:
        fd=os.open(str(path),os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size>MAX_SAVE:
            raise ReportError('INVALID_SAVE_TYPE_OR_SIZE')
        if hasattr(os,'getuid') and info.st_uid!=os.getuid():
            raise ReportError('SAVE_NOT_OWNED_BY_USER')
        if stat.S_IMODE(info.st_mode)&0o077:
            raise ReportError('SAVE_PERMISSIONS_NOT_PRIVATE')
        raw=os.read(fd,MAX_SAVE+1)
    except OSError as exc:
        raise ReportError('SAVE_UNAVAILABLE') from exc
    finally:
        if fd is not None: os.close(fd)
    if len(raw)>MAX_SAVE: raise ReportError('SAVE_TOO_LARGE')
    doc=_strict_json(raw)
    if type(doc) is not dict or set(doc)!={'schema','protocol','instance_id','journal','state_sha256','document_sha256'}:
        raise ReportError('UNRECOGNIZED_SAVE_ENVELOPE')
    if doc['schema']!='tia-tutorial-save/v1' or doc['protocol']!='tia-native-tutorial/v1':
        raise ReportError('UNRECOGNIZED_SAVE_SCHEMA')
    if type(doc['journal']) is not list or not 1<=len(doc['journal'])<=512:
        raise ReportError('INVALID_JOURNAL')
    if not isinstance(doc['document_sha256'],str) or doc['document_sha256']!=_canon_hash({k:v for k,v in doc.items() if k!='document_sha256'}):
        raise ReportError('SAVE_DOCUMENT_DIGEST_MISMATCH')
    return raw,doc,hashlib.sha256(raw).hexdigest()


def _private_write(path: Path, data: bytes):
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
    with os.fdopen(fd,'wb') as target:
        target.write(data)
        target.flush()
        os.fsync(target.fileno())


def safe_title(question:Any, position:int)->str:
    """No title is required for source integrity; never infer from screenshots."""
    if type(question) is dict:
        obj=question.get('question') if type(question.get('question')) is dict else question
        val=obj.get('title')
        if type(val) is str and 1<=len(val)<=240: return val
    return 'Question '+str(position)


def _get_question_names(state:dict):
    reh=state.get('rehearsal')
    if type(reh) is dict and type(reh.get('questions')) is list:
        qs=reh['questions']
        return [safe_title(q,i+1) for i,q in enumerate(qs[:3])]+['Question '+str(i+1) for i in range(len(qs),3)]
    return ['Question 1','Question 2','Question 3']


def _is_committed(value):
    """Only actual restored Host artifact membership counts; UI labels do not."""
    return type(value) is dict and bool(value)


def compile_session(state:dict, assessments:dict, doc:dict, source_sha:str)->dict:
    if type(state) is not dict or type(assessments) is not dict: raise ReportError('HOST_STATE_CONTRACT_MISSING')
    if type(doc) is not dict or type(doc.get('journal')) is not list: raise ReportError('INVALID_DOCUMENT')
    names=_get_question_names(state)
    def lookup(i):
        if str(i) in assessments: return assessments[str(i)]
        if i in assessments: return assessments[i]
        return None
    entries=[]
    for i in range(3):
        committed=_is_committed(lookup(i))
        entries.append({'question_index':i,'title':names[i],
                        'proposal_status':'PENDING_HUMAN_REVIEW' if committed else 'NOT_EVALUATED',
                        'live_proposal_recorded':committed,
                        'verified_sql_status':'NOT_ASSERTED_BY_THIS_REPORT',
                        'final_grade':'NOT_SCORED',
                        'metric_approval':'NOT_PERFORMED'})
    n=sum(int(x['live_proposal_recorded']) for x in entries)
    journal=doc['journal']
    commits=[j for j in journal if type(j) is dict and j.get('action')=='native_commit_evaluator' and j.get('outcome')=='OK']
    out={'schema':'tia-e4d03-session-report/v1','source_sha256':source_sha,
         'save_integrity':'DOCUMENT_DIGEST_VALIDATED_NOT_AUTHENTICATED',
         'source_journal_entries':len(journal),'successful_evaluator_commit_events':len(commits),
         'recovered_evaluator_proposals':n,'expected_questions':3,
         'questions':entries,'session_evaluator_status':'ALL_PROPOSALS_RECORDED_REVIEW_PENDING' if n==3 else 'PARTIAL_PROPOSALS',
         'session_final_score_status':'NOT_SCORED',
         'policies':{'historical':'11_dimension_T01_T05_C01_C06_60_40_PROPOSAL',
                     'experimental':'12_dimension_T1_T4_C1_C4_P1_P4_70_20_10_SEPARATE',
                     'crosswalk':'NOT_APPROVED','automatic_grade':'DISABLED',
                     'model_rationales':'NOT_EXPORTED','candidate_text':'NOT_EXPORTED'},
         'quality_gates':{'real_model_transport_independently_verified':False,
                          'human_semantic_approval':False,
                          'sql_execution_independently_verified':False,
                          'full_session_product_acceptance':False},
         'restrictions':{'real_model_calls':0,'original_save_modified':False,
                         'repository_commit':False,'candidate_competence_grade_certified':False}}
    return out


def render_html(report:dict)->str:
    esc=lambda s:html.escape(str(s),quote=True)
    rows='\n'.join('''<article class="question"><div class="num">Q{no}</div><div class="body"><h2>{name}</h2>
    <p class="label">{state}</p><p class="minor">Final grade: NOT_SCORED · No candidate text exported · No re-evaluation</p></div></article>'''.format(no=q['question_index']+1,name=esc(q['title']),state=esc(q['proposal_status'])) for q in report['questions'])
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TIA · Full-session Evaluator</title><style>
:root{color-scheme:light;font-family:system-ui,-apple-system,sans-serif;color:#18332d;background:#f5f6f1}*{box-sizing:border-box}body{max-width:980px;margin:50px auto;padding:0 22px}h1{font-size:2.25rem;margin:0 0 14px}.sub{color:#5d6d66;line-height:1.55}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:30px 0}.stat,.question,.note{background:white;border:1px solid #d8e3d9;border-radius:15px;padding:22px}.stat strong{display:block;font-size:2rem;margin-bottom:5px}.stat span,.minor{color:#65726c;font-size:.86rem}.question{display:flex;gap:22px;margin:12px 0}.num{font-weight:800;color:#30765b;font-size:1.4rem;min-width:35px}.question h2{font-size:1.15rem;margin:0 0 12px}.question p{margin:4px 0}.label{font-size:.86rem;font-weight:650;color:#2b6f50}.note{margin-top:25px;line-height:1.6}.note strong{color:#354c43}code{overflow-wrap:anywhere}.warn{color:#8b5b19;font-weight:700}@media(max-width:650px){.stats{grid-template-columns:1fr}.stat strong{font-size:1.5rem}}
</style></head><body><h1>TIA · Full-session Evaluator</h1><p class="sub">Private local status report reconstructed from a verified save copy. It is a session-level product report, not a benchmark, employment prediction, or validated competence grade.</p>
<section class="stats"><div class="stat"><strong>__COUNT__/3</strong><span>Recorded live evaluator proposals</span></div><div class="stat"><strong>__JOURNAL__</strong><span>Source journal entries</span></div><div class="stat"><strong>NOT_SCORED</strong><span>Final grade</span></div></section>
__ROWS__
<section class="note"><strong>Evidence governance</strong><p>Historical 11-criterion Technical/Communication framework (proposed 60/40) and experimental 12-metric framework (70/20/10) are separate. This report neither crosswalks nor promotes a model proposal to an approved score.</p><p><span class="warn">__STATUS__</span> · A recorded AI proposal requires source-grounded review before it can be treated as an accepted assessment. Missing evidence remains missing, not zero.</p><p><small>Original save SHA-256: <code>__DIGEST__</code></small></p></section></body></html>'''.replace('__COUNT__',str(report['recovered_evaluator_proposals'])).replace('__JOURNAL__',str(report['source_journal_entries'])).replace('__ROWS__',rows).replace('__STATUS__',esc(report['session_evaluator_status'])).replace('__DIGEST__',esc(report['source_sha256']))


async def restore_on_copy(raw:bytes, root:Path):
    """Host replays journal in scratch copy; real save file stays untouched."""
    runtime_root = Path(__file__).resolve().parents[1]
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))
    from tia_runtime.app_host import TutorialHost
    with tempfile.TemporaryDirectory(prefix='tia-e4d03-',dir=None) as tmp:
        place=Path(tmp)
        os.chmod(place,0o700)
        dst=place/EXPECTED_SAVE
        _private_write(dst,raw)
        host=await TutorialHost.open(place)
        try:
            if getattr(host,'_recovery_error',None): raise ReportError('HOST_RECOVERY_REJECTED')
            state=host.state()
            assessments=getattr(host,'_evaluator_assessments',None)
            if type(assessments) is not dict: raise ReportError('HOST_EVALUATOR_ASSESSMENT_MAP_MISSING')
            return state,assessments
        finally:
            host.close()


def report_from_save(save:Path, outdir:Path, restore_fn=restore_on_copy):
    os.umask(0o077)
    raw,doc,save_sha=read_save_bytes(save)
    # Input bytes are passed into the ONLY replay sandbox; no direct original-path Host open.
    state,assessments=asyncio.run(restore_fn(raw,outdir))
    result=compile_session(state,assessments,doc,save_sha)
    if outdir.exists() or outdir.is_symlink(): raise ReportError('OUTPUT_DIR_ALREADY_EXISTS')
    outdir.mkdir(mode=0o700,parents=False)
    _private_write(outdir/'TIA_SESSION_REPORT.json',(json.dumps(result,indent=2,ensure_ascii=False)+'\n').encode('utf8'))
    _private_write(outdir/'TIA_SESSION_REPORT.html',render_html(result).encode('utf8'))
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--save',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args(argv)
    try:
        result=report_from_save(args.save.expanduser(),args.output_dir.expanduser())
    except (ReportError,OSError,ValueError,KeyError,RuntimeError) as ex:
        name=ex.args[0] if isinstance(ex,ReportError) else 'RUNTIME_OR_IO_ERROR'
        print('E4D03_EXPORT_REFUSED='+name,file=sys.stderr)
        return 2
    print('E4D03_SOURCE_INTEGRITY=PASS')
    print('E4D03_EVALUATOR_PROPOSALS='+str(result['recovered_evaluator_proposals'])+'/3')
    print('E4D03_SESSION_STATE='+result['session_evaluator_status'])
    print('E4D03_FINAL_GRADE=NOT_SCORED')
    print('E4D03_HTML='+str(args.output_dir.expanduser()/'TIA_SESSION_REPORT.html'))
    print('E4D03_NO_MODEL_CALLS=YES ORIGINAL_SAVE_UNMODIFIED=YES')
    return 0

if __name__=='__main__': raise SystemExit(main())
