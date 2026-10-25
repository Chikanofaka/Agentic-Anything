"""Swift compiled Native -> localhost Mock HTTP -> Python Host 12-D review UAT."""
from __future__ import annotations
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tia_runtime.evaluator_v1_native_transaction import OfflineEvaluatorTransactionHarness
from tia_runtime.evaluator_v1_native_wire import (wire_request, mock_wire_response, commit_from_native_wire)
from tia_runtime.evaluator_v1_semantic_contract import DIMENSIONS, PROPOSAL_SCHEMA


def fixture():
    plan = {'status':'COMPLETE', 'questions':[{'title':f'DEMO {i}','content_sha256':str(i+1)*64} for i in range(3)],
        'results':[{'index':i,'outcome':'SUBMITTED_UNVERIFIED','question_sha256':str(i+1)*64,
        'session':{'events':[{'id':f'demo-q{i}:3','actor':'candidate','kind':'plan',
        'payload':{'text':'This is synthetic evidence for a window-function plan.'}}]}} for i in range(3)]}
    return plan, [{'action':'rehearsal_complete','seq':1}]


def run(binary):
    plan,journal=fixture()
    harness=OfflineEvaluatorTransactionHarness()
    ticket=harness.prepare_mock(plan,journal,0,consent=True)
    proposal={'schema': PROPOSAL_SCHEMA, 'role':'evaluator','source_sha256':ticket['source_sha256'],
        'dimensions':[{'id':metric,'anchor':2 if metric=='T2' else None,
        'evidence_ids':['demo-q0:3'] if metric=='T2' else [],
        'reason':'Synthetic test only, no technical correctness assessment.' if metric=='T2' else 'No rating evidence observed.',
        'confidence':'LOW' if metric=='T2' else 'NOT_ASSESSED'} for metric in DIMENSIONS],
        'summary':'Offline synthetic native-wire proposal; not a real model evaluation.'}
    payload = mock_wire_response(ticket, json.dumps(proposal,sort_keys=True))
    count={'requests':0}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):pass
        def do_POST(self):
            if self.path != '/tia/evaluator/mock':self.send_error(404);return
            length=self.headers.get('Content-Length','0')
            try:n=int(length)
            except ValueError:self.send_error(400);return
            if not 0 < n <= 8192:self.send_error(413);return
            body=self.rfile.read(n)
            try:decoded=json.loads(body)
            except ValueError:self.send_error(400);return
            if decoded != wire_request(ticket) or 'Authorization' in self.headers:
                self.send_error(400);return
            count['requests']+=1
            content=json.dumps(payload,sort_keys=True).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(content)))
            self.end_headers();self.wfile.write(content)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        proc=subprocess.run([str(binary),'--mock-port',str(server.server_port)],
            input=json.dumps(wire_request(ticket)), text=True, capture_output=True, timeout=16)
        if proc.returncode != 0:
            raise RuntimeError('NATIVE_MOCK_WIRE_FAILED '+proc.stdout[-400:]+' '+proc.stderr[-300:])
        committed=commit_from_native_wire(harness,plan,journal,ticket,proc.stdout.strip())
        result={'stage':'E4D-02C1B1A','status':committed['status'],
        'native_mock_http_requests':count['requests'], 'actual_paid_requests':0,
        'dimension_count':len(committed['review_packet']['dimensions']),
        'cited_dimensions':sum(row['status']=='REVIEW_REQUIRED' for row in committed['review_packet']['dimensions']),
        'verified_competency_score':None,'native_production_bridge_enabled':False,
        'historical_saved_records_mutated':False,
        'source_sha256':committed['source_sha256']}
        return result
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)


def main():
    p=argparse.ArgumentParser();p.add_argument('--swift-binary',type=Path,required=True)
    args=p.parse_args();print(json.dumps(run(args.swift_binary),indent=2))
if __name__=='__main__':main()
