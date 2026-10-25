"""Actual Swift executable + Python loopback Mock HTTP negative UAT.
No external API, credentials, real evaluation, saved record or official SQL test.
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from tia_runtime.evaluator_v1_native_transaction import OfflineEvaluatorTransactionHarness
from tia_runtime.evaluator_v1_native_wire import wire_request, mock_wire_response
from tia_runtime.evaluator_v1_semantic_contract import DIMENSIONS, PROPOSAL_SCHEMA


def sample_ticket():
    plan={'status':'COMPLETE','questions':[{'title':f'S{i}','content_sha256':str(i+1)*64} for i in range(3)],
          'results':[{'index':i,'outcome':'SUBMITTED_UNVERIFIED','question_sha256':str(i+1)*64,
          'session':{'events':[{'id':f'sq{i}-c','actor':'candidate','kind':'plan',
          'payload':{'text':'Synthetic semantic evidence.'}}]}} for i in range(3)]}
    h=OfflineEvaluatorTransactionHarness()
    return h.prepare_mock(plan,[{'action':'rehearsal_complete','seq':1}],0,consent=True)


@unittest.skipUnless(shutil.which('swiftc'),'swiftc required for Native Swift mock HTTP tests')
class NativeSwiftHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='tia02c1b1a_swift_')
        base=Path(__file__).resolve().parents[1]
        cls.binary=Path(cls.tmp.name)/'evaluator-mock-wire'
        result=subprocess.run(['swiftc','-swift-version','6','-o',str(cls.binary),
          str(base/'native/EvaluatorMockHTTPWire.swift')],capture_output=True,text=True,timeout=40)
        if result.returncode:raise RuntimeError('SWIFT_COMPILE_FAILED '+result.stderr[-2000:])
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def call(self, *, mutation=None, status=200, redirect=False):
        ticket=sample_ticket()
        p={'schema':PROPOSAL_SCHEMA,'role':'evaluator','source_sha256':ticket['source_sha256'],
           'dimensions':[{'id':d,'anchor':None,'evidence_ids':[],
             'reason':'Not independently assessed.', 'confidence':'NOT_ASSESSED'} for d in DIMENSIONS],
           'summary':'A synthetic response with no scores or claims.'}
        response=mock_wire_response(ticket,json.dumps(p))
        if mutation:response[mutation]='wrong-value'
        state={'request':None,'auth':False}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_POST(self):
                state['auth']='Authorization' in self.headers
                size=int(self.headers.get('Content-Length',0))
                state['request']=json.loads(self.rfile.read(size))
                if redirect:
                    self.send_response(302);self.send_header('Location','https://api.openai.com/v1/responses');self.end_headers();return
                body=json.dumps(response).encode()
                self.send_response(status);self.send_header('Content-Length',str(len(body)));self.end_headers()
                self.wfile.write(body)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            cp=subprocess.run([str(self.binary),'--mock-port',str(server.server_port)],
              input=json.dumps(wire_request(ticket)),text=True,capture_output=True,timeout=17)
            return ticket,state,cp
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)

    def test_real_swift_loopback_roundtrip(self):
        ticket,state,p=self.call()
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(state['request'],wire_request(ticket))
        self.assertFalse(state['auth'])
        self.assertEqual(json.loads(p.stdout)['source_sha256'],ticket['source_sha256'])

    def test_swift_rejects_digest_mismatch(self):
        _,_,p=self.call(mutation='source_sha256')
        self.assertEqual(p.returncode,2)
        self.assertEqual(json.loads(p.stdout)['code'],'MOCK_HTTP_RESPONSE_REJECTED')

    def test_swift_rejects_non_200(self):
        _,_,p=self.call(status=429)
        self.assertEqual(p.returncode,2)

    def test_swift_does_not_follow_external_redirect(self):
        _,_,p=self.call(redirect=True)
        self.assertEqual(p.returncode,2)

    def test_swift_rejects_extra_authority(self):
        _,_,p=self.call(mutation='grade')
        self.assertEqual(p.returncode,2)

if __name__=='__main__':unittest.main()
