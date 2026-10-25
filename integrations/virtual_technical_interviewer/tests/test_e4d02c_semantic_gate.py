"""Pure local tests for the additive 02C human semantic gate."""
import importlib.util
import json
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

TARGET = Path(__file__).resolve().parents[1] / 'scripts' / 'e4d02c_semantic_gate.py'
spec = importlib.util.spec_from_file_location('e4d02c_semantic_gate', TARGET)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fake_doc():
    v = {'schema': audit.EXPECTED_SCHEMA,
         'protocol': audit.EXPECTED_PROTOCOL,
         'instance_id': 'a'*32, 'journal': [
             {'action':'rehearsal_submit','params':{'kind':'implement','text':'PRIVATE_SQL_MARKER','question_index':0},'outcome':'OK','tick_seconds':1.0},
             {'action':'native_commit_evaluator','params':{'private_reply':'PRIVATE_MODEL_MARKER','question_index':0},'outcome':'OK','tick_seconds':2.0}
         ], 'state_sha256':'b'*64}
    v['document_sha256'] = audit.digest_object(v)
    return v


class GateContracts(unittest.TestCase):
    def test_integrity_accepts_valid_save(self):
        x=audit.scan(fake_doc(),'1'*64)
        self.assertTrue(x['document_sha256_valid'])
        self.assertEqual(len(x['evaluator_commits_metadata']),1)
        self.assertEqual(x['gate'],'HUMAN_SEMANTIC_REVIEW_REQUIRED')

    def test_wrong_digest_rejected(self):
        x=fake_doc();x['journal'][0]['outcome']='FORGED'
        with self.assertRaisesRegex(audit.GateError,'SAVE_DIGEST_MISMATCH'):
            audit.scan(x,'1'*64)

    def test_no_raw_text_or_reply_in_report(self):
        result=audit.scan(fake_doc(),'1'*64)
        s=json.dumps(result)+audit.report_markdown(result)
        self.assertNotIn('PRIVATE_SQL_MARKER',s)
        self.assertNotIn('PRIVATE_MODEL_MARKER',s)
        self.assertIn('C01_REVIEW',s)
        self.assertIn('C04_REVIEW',s)
        self.assertIn('T02_REVIEW',s)

    def test_duplicate_json_rejected(self):
        with self.assertRaises(audit.GateError):
            audit._strict_json(b'{"foo":1,"foo":2}')

    def test_nan_json_rejected(self):
        with self.assertRaises(audit.GateError):
            audit._strict_json(b'{"foo":NaN}')

    def test_wrong_schema_fails_closed(self):
        x=fake_doc();x['schema']='other'
        x['document_sha256']=audit.digest_object({k:v for k,v in x.items() if k!='document_sha256'})
        with self.assertRaisesRegex(audit.GateError,'UNRECOGNIZED_SAVE_SCHEMA'):
            audit.scan(x,'1'*64)

    def test_symlink_save_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'save.json'; b=Path(d)/'link.json'
            a.write_text('{}');b.symlink_to(a)
            with self.assertRaisesRegex(audit.GateError,'SAVE_SYMLINK_REJECTED'):
                audit.read_local_save(b)

    def test_end_to_end_cli_private_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); src=root/'save.json';out=root/'private_results'
            src.write_text(json.dumps(fake_doc()))
            rc=audit.main(['--save',str(src),'--output-dir',str(out)])
            self.assertEqual(rc,0)
            self.assertEqual(out.stat().st_mode & 0o777,0o700)
            for file in out.iterdir():
                self.assertEqual(file.stat().st_mode & 0o777,0o600)
                self.assertNotIn('PRIVATE_SQL_MARKER',file.read_text())
            self.assertTrue((out/'review_receipt.json').exists())
            self.assertTrue((out/'HUMAN_REVIEW_Q1.md').exists())

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'no-overwrite.txt';out.write_text('retained')
            with self.assertRaisesRegex(audit.GateError,'OUTPUT_ALREADY_EXISTS'):
                audit.write_private(out,b'overwrite')
            self.assertEqual(out.read_text(),'retained')

    def test_no_commit_is_review_required_not_pass(self):
        x=fake_doc();x['journal']=x['journal'][:1]
        x['document_sha256']=audit.digest_object({k:v for k,v in x.items() if k!='document_sha256'})
        r=audit.scan(x,'1'*64)
        self.assertEqual(len(r['evaluator_commits_metadata']),0)
        self.assertTrue(any('NO_EVALUATOR_COMMIT' in s for s in r['review_required']))


if __name__=='__main__': unittest.main()
