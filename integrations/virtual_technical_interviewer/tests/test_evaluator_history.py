"""E4 private export history remains metadata-only; no API or database calls."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts'/'history_ledger.py'
spec=importlib.util.spec_from_file_location('tia_history_ledger_local_test',SCRIPT)
h=importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def sample():
    return {'schema':'tia-tutorial-export/v1','privacy':'TOP_SECRET_INTERVIEW_ANSWER',
        'rehearsal':{'status':'COMPLETE','results':[{}, {}, {}]},
        'evidence_scorecard':{'summary':{'latest_sql_locally_verified_questions':1}},
        'evaluator_report':{'full_scheme':{
            'schema':'tia-evaluator-full-scheme/v1','final_overall_score':'NOT_SCORED',
            'technical':{'covered_weight':23},'communication':{'covered_weight':7},
            'blocked_proposal_dimensions':4}},
        'smart_progress_summary':{'recorded_attempts':2}}

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.export=self.root/'export.json';self.ledger=self.root/'local-ledger.json'
        self.export.write_text(json.dumps(sample()),encoding='utf-8')
    def test_frozen_export_produces_metadata(self):
        entry=h.validate_export(self.export)
        self.assertEqual(entry['technical_coverage_weight'],23)
        self.assertFalse(entry['formally_scored'])
        self.assertNotIn('TOP_SECRET',str(entry))
    def test_record_and_dedupe_do_not_store_private_text(self):
        from types import SimpleNamespace
        args=SimpleNamespace(ledger=str(self.ledger),record=str(self.export),list=False)
        h.execute(args);h.execute(args)
        doc=h.read_ledger(self.ledger)
        self.assertEqual(len(doc['records']),1)
        self.assertNotIn('TOP_SECRET',self.ledger.read_text())
    def test_rejects_fake_formal_grade(self):
        obj=sample();obj['evaluator_report']['full_scheme']['final_overall_score']=95
        self.export.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,'UNTRUSTED_FORMAL_SCORE_CLAIM'):
            h.validate_export(self.export)
    def test_refuses_incomplete_rehearsal(self):
        obj=sample();obj['rehearsal']['status']='ACTIVE';self.export.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,'NO_CLOSED_REHEARSAL'):
            h.validate_export(self.export)
    def test_refuses_external_symlink(self):
        link=self.root/'outside.json';link.symlink_to(self.export)
        with self.assertRaisesRegex(ValueError,'EXPORT_FILE_UNSAFE'):
            h.validate_export(link)
    def test_refuses_invalid_counters(self):
        obj=sample();obj['evaluator_report']['full_scheme']['technical']['covered_weight']=181
        self.export.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,'INVALID_COUNTER_technical'):
            h.validate_export(self.export)
    def test_diff_is_coverage_not_ability_score(self):
        from types import SimpleNamespace
        args=SimpleNamespace(ledger=str(self.ledger),record=str(self.export),list=False)
        h.execute(args)
        obj=sample();obj['evaluator_report']['full_scheme']['technical']['covered_weight']=36
        self.export.write_text(json.dumps(obj))
        h.execute(args)
        self.assertEqual(len(h.read_ledger(self.ledger)['records']),2)
        self.assertEqual(h.read_ledger(self.ledger)['records'][-1]['technical_coverage_weight'],36)

if __name__=='__main__':unittest.main()
