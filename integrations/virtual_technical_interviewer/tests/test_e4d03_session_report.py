"""Offline 3-question report policy and packaging tests; no actual provider call."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

src=Path(__file__).resolve().parents[1]/'scripts'/'e4d03_session_report.py'
spec=importlib.util.spec_from_file_location('reporter',src)
r=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def example():
    d={'schema':'tia-tutorial-save/v1','protocol':'tia-native-tutorial/v1',
       'instance_id':'a'*32,'journal':[{'action':'rehearsal_submit','outcome':'OK',
          'params':{'private_candidate_text':'PRIVATE_CANDIDATE_SQL'},'tick_seconds':1.0}],
       'state_sha256':'c'*64}
    d['document_sha256']=r._canon_hash(d)
    return d


def app_state():
    return {'rehearsal':{'questions':[{'title':'Question 1: <script>bad()</script>'},
                                         {'question':{'title':'Question 2'}},{'title':'Question 3'}]}}


class ProductContracts(unittest.TestCase):
    def test_one_question_report_progress(self):
        v=r.compile_session(app_state(),{'0':{'proposed_ratings':[1]}},example(),'1'*64)
        self.assertEqual(v['recovered_evaluator_proposals'],1)
        self.assertEqual([q['proposal_status'] for q in v['questions']],['PENDING_HUMAN_REVIEW','NOT_EVALUATED','NOT_EVALUATED'])
    def test_three_complete_proposals_never_certifies_grade(self):
        v=r.compile_session(app_state(),{str(i):{'artifact':'recorded'} for i in range(3)},example(),'1'*64)
        self.assertEqual(v['session_evaluator_status'],'ALL_PROPOSALS_RECORDED_REVIEW_PENDING')
        self.assertEqual(v['session_final_score_status'],'NOT_SCORED')
        self.assertFalse(v['quality_gates']['full_session_product_acceptance'])
    def test_no_proposals_remains_partial(self):
        self.assertEqual(r.compile_session(app_state(),{},example(),'a'*64)['recovered_evaluator_proposals'],0)
    def test_title_escapes_html(self):
        html=r.render_html(r.compile_session(app_state(),{},example(),'2'*64))
        self.assertNotIn('<script>',html)
        self.assertIn('&lt;script&gt;',html)
    def test_no_candidate_text_model_reply_in_report(self):
        v=r.compile_session(app_state(),{'0':{'private_reply':'SECRET_MODEL_PAYLOAD'}},example(),'2'*64)
        text=json.dumps(v)+r.render_html(v)
        self.assertNotIn('SECRET_MODEL_PAYLOAD',text)
        self.assertNotIn('PRIVATE_CANDIDATE_SQL',text)
    def test_source_permissions_require_private(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'tutorial-v1.json';f.write_text(json.dumps(example())); f.chmod(0o644)
            with self.assertRaisesRegex(r.ReportError,'SAVE_PERMISSIONS_NOT_PRIVATE'):r.read_save_bytes(f)
    def test_read_save_integrity(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'tutorial-v1.json';f.write_text(json.dumps(example()));f.chmod(0o600)
            raw,doc,sha=r.read_save_bytes(f)
            self.assertEqual(doc['schema'],'tia-tutorial-save/v1')
            self.assertEqual(len(sha),64)
    def test_digest_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'tutorial-v1.json';a=example();a['journal'][0]['outcome']='FORGED'
            f.write_text(json.dumps(a));f.chmod(0o600)
            with self.assertRaisesRegex(r.ReportError,'SAVE_DOCUMENT_DIGEST_MISMATCH'):r.read_save_bytes(f)
    def test_json_duplicate_rejected(self):
        with self.assertRaises(r.ReportError):r._strict_json(b'{"a":1,"a":2}')
    def test_json_nan_rejected(self):
        with self.assertRaises(r.ReportError):r._strict_json(b'{"a":NaN}')
    def test_symlink_save_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'real';f.write_text('{}');link=Path(d)/'link';link.symlink_to(f)
            with self.assertRaisesRegex(r.ReportError,'SYMLINK_SAVE_REFUSED'):r.read_save_bytes(link)
    def test_report_writes_privately_without_modifying_save(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'tutorial-v1.json';f.write_text(json.dumps(example()));f.chmod(0o600)
            before=f.read_bytes()
            async def fake_restore(raw,_):
                self.assertEqual(raw,before)
                return app_state(),{'0':{'assessed':True}}
            out=Path(d)/'new-report'
            result=r.report_from_save(f,out,restore_fn=fake_restore)
            self.assertEqual(result['recovered_evaluator_proposals'],1)
            self.assertEqual(before,f.read_bytes())
            self.assertEqual(out.stat().st_mode&0o777,0o700)
            for artifact in out.iterdir():self.assertEqual(artifact.stat().st_mode&0o777,0o600)
            self.assertIn('Question 2',(out/'TIA_SESSION_REPORT.html').read_text())
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'tutorial-v1.json';f.write_text(json.dumps(example()));f.chmod(0o600)
            async def fake_restore(raw,_):return app_state(),{}
            out=Path(d)/'occupied';out.mkdir()
            with self.assertRaisesRegex(r.ReportError,'OUTPUT_DIR_ALREADY_EXISTS'):
                r.report_from_save(f,out,restore_fn=fake_restore)
    def test_60_40_and_70_20_10_not_mixed(self):
        v=r.compile_session(app_state(),{},example(),'1'*64)
        self.assertIn('11_dimension',v['policies']['historical'])
        self.assertIn('12_dimension',v['policies']['experimental'])
        self.assertEqual(v['policies']['crosswalk'],'NOT_APPROVED')
    def test_no_unknown_rating_used(self):
        v=r.compile_session(app_state(),{'0':{'model_proposed_total':9999}},example(),'a'*64)
        self.assertEqual(v['session_final_score_status'],'NOT_SCORED')
    def test_three_questions_even_if_host_missing_rehearsal(self):
        v=r.compile_session({}, {},example(),'a'*64)
        self.assertEqual(len(v['questions']),3)
        self.assertEqual(v['questions'][2]['title'],'Question 3')
    def test_bad_state_contract_rejected(self):
        with self.assertRaises(r.ReportError):r.compile_session([],{},example(),'a'*64)

if __name__=='__main__': unittest.main()
