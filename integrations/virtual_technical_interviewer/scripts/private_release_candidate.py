#!/usr/bin/env python3
"""Mac-only private engineering release candidate. NEVER publishes/signs/notarizes."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

REPO_REL = 'integrations/virtual_technical_interviewer'
BLOCKERS = ['HUMAN_UAT_NOT_RUN','FORMAL_RUBRIC_CALIBRATION_NOT_APPROVED',
            'INDEPENDENT_SQL_CERTIFICATION_INCOMPLETE','PUBLICATION_AUTHORIZATION_NOT_GRANTED',
            'SIGNED_NOTARIZED_DISTRIBUTION_NOT_VERIFIED']
SECRET = re.compile(rb'(?:sk-(?:proj-)?[A-Za-z0-9_\-]{20,}|(?i:OPENAI_API_KEY)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{20,})')
TEXT_EXT = {'.md','.json','.js','.py','.txt','.html','.xml','.plist','.sh','.swift','.css','.env'}


def digest(file):
    h=hashlib.sha256()
    with open(file,'rb') as f:
        while True:
            b=f.read(1024*1024)
            if not b:break
            h.update(b)
    return h.hexdigest()


def safety_scan(app):
    if not app.is_dir() or app.is_symlink():raise ValueError('APP_BUNDLE_MISSING_OR_SYMLINK')
    count=0
    base=app.resolve()
    for p in app.rglob('*'):
        if p.is_symlink():
            target=p.resolve()
            if not target.is_relative_to(base):raise ValueError('APP_EXTERNAL_SYMLINK')
            continue
        if p.is_dir():continue
        if p.name=='.env' or p.suffix in ('.pem','.key','.p12','.p8'):
            raise ValueError('CREDENTIAL_LIKE_FILE_IN_APP')
        if p.suffix.lower() in TEXT_EXT and p.stat().st_size<4_000_000:
            if SECRET.search(p.read_bytes()):raise ValueError('POSSIBLE_EMBEDDED_API_SECRET')
        count+=1
    if count==0:raise ValueError('EMPTY_APP_BUNDLE')
    return count


def release(repo,gate_receipt,output):
    if platform.system()!='Darwin':raise ValueError('MACOS_REQUIRED')
    target=repo/REPO_REL
    if not (target/'ui/app.js').is_file() or not (target/'tia_runtime/evaluator_full_scheme.py').is_file():
        raise ValueError('E3_SCHEME_SOURCE_NOT_PRESENT')
    js=(target/'ui/app.js').read_text(encoding='utf-8')
    for x in ('function evaluatorCloseoutPanel()', 'function fullEvaluatorSchemePanel()',
              'function fullInterviewTranscript()'):
        if x not in js:raise ValueError('CLOSEOUT_UI_INCOMPLETE')
    if not gate_receipt.is_file() or gate_receipt.is_symlink():raise ValueError('AUTOMATED_GATE_RECEIPT_MISSING')
    receipt=json.loads(gate_receipt.read_text(encoding='utf-8'))
    if receipt.get('status')!='AUTOMATED_ENGINEERING_PASS' or receipt.get('human_uat')!='NOT_RUN':
        raise ValueError('AUTOMATED_GATE_NOT_PASS')
    if receipt.get('app_js_sha256')!=digest(target/'ui/app.js'):
        raise ValueError('RELEASE_SOURCE_CHANGED_AFTER_GATE')
    app=target/'dist/Technical Interview Lab.app'
    files=safety_scan(app)
    if shutil.which('ditto') is None:raise ValueError('DITTO_UNAVAILABLE')
    if output.exists():raise ValueError('RELEASE_OUTPUT_ALREADY_EXISTS')
    output.mkdir(mode=0o700,parents=True)
    archive=output/'Technical_Interview_Lab_Private_Engineering_Candidate.zip'
    subprocess.run(['ditto','-c','-k','--keepParent',str(app),str(archive)],check=True)
    archive.chmod(0o600)
    signed=subprocess.run(['codesign','--verify','--deep','--strict',str(app)],capture_output=True,text=True)
    manifest={
        'schema':'tia-private-engineering-release-candidate/v1',
        'status':'PRIVATE_ENGINEERING_CANDIDATE_NOT_PUBLIC_RELEASE',
        'artifact':archive.name,'archive_sha256':digest(archive),
        'source_ui_sha256':receipt['app_js_sha256'],
        'native_source_sha256':digest(target/'tia_runtime/native_evaluator.py'),
        'bundle_scanned_regular_files':files,
        'automatic_tests':'PASS_PER_LOCAL_GATE_RECEIPT',
        'codesign_verification':'PASS' if signed.returncode==0 else 'NOT_VERIFIED',
        'human_uat':'NOT_RUN','model_paid_calls':0,'release_blockers':BLOCKERS,
        'publication':'NOT_AUTHORIZED',
        'notes':['Bundle is private and may be unsigned or unnotarized.',
                 'There is no certified interview grade. Source exports may contain personal content: do not bundle them.',
                 'This script does not publish, sign, notarize or contact any app store.'],
    }
    m=output/'PRIVATE_RELEASE_MANIFEST.json'
    m.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    m.chmod(0o600)
    print('TIA_PRIVATE_RELEASE_CANDIDATE=PACKAGED')
    print('ARCHIVE='+str(archive));print('ARCHIVE_SHA256='+manifest['archive_sha256'])
    print('CODESIGN='+manifest['codesign_verification']+' PUBLICATION=NOT_AUTHORIZED HUMAN_UAT=NOT_RUN')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--repo',required=True);p.add_argument('--gate-receipt',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    try:release(Path(a.repo).expanduser().resolve(),Path(a.gate_receipt).expanduser(),Path(a.output).expanduser())
    except (ValueError,PermissionError,OSError,subprocess.CalledProcessError,json.JSONDecodeError) as e:
        print('TIA_PRIVATE_RELEASE_CANDIDATE=HOLD REASON='+str(e));sys.exit(2)
