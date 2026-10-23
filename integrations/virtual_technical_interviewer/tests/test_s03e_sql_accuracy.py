"""S03-E2.5A: strict fixture validation, honest comparison, no database side effects in unit tests."""
import copy
import json
import tempfile
import unittest
from unittest.mock import patch

from tia_runtime import sql_accuracy as sa


def demo():
    return {'schema': sa.SCHEMA, 'fixture_id': 'synthetic-bus-001',
            'question_sha256': 'a' * 64, 'environment': 'POSTGRESQL',
            'tables': [{'name': 'Queue', 'columns': [
                {'name': 'person_id', 'type': 'INTEGER'},
                {'name': 'person_name', 'type': 'TEXT'},
                {'name': 'weight', 'type': 'INTEGER'},
                {'name': 'turn', 'type': 'INTEGER'}],
                'rows': [[5, 'Alice', 250, 1], [2, 'Bob', 175, 2],
                         [3, 'Alex', 350, 3], [6, 'John', 400, 4]]}],
            'expected': {'columns': ['person_name'], 'rows': [['Alex']],
                         'order_sensitive': False}}


def blob(value):
    return json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode()


class SqlAccuracyTests(unittest.TestCase):
    def test_valid_fixture_digest_is_exact_source_bytes(self):
        f = demo()
        a, hash_a = sa.validate_fixture(blob(f))
        b, hash_b = sa.validate_fixture(json.dumps(f, indent=2).encode())
        self.assertEqual(a, b)
        self.assertNotEqual(hash_a, hash_b)

    def test_reject_unknown_fixture_fields(self):
        f = demo(); f['magical_pass'] = True
        with self.assertRaisesRegex(sa.AccuracyError, 'INVALID_FIXTURE_CONTRACT'):
            sa.validate_fixture(blob(f))

    def test_reject_duplicate_json_keys(self):
        raw = blob(demo()).replace(b'"fixture_id":', b'"fixture_id":"duplicate","fixture_id":')
        with self.assertRaisesRegex(sa.AccuracyError, 'INVALID_FIXTURE_JSON'):
            sa.validate_fixture(raw)

    def test_reject_injection_identifier_and_type(self):
        for field, value in [('name', 'Queue; DROP DATABASE postgres'), ('name', '"Queue"')]:
            f = demo(); f['tables'][0][field] = value
            with self.assertRaises(sa.AccuracyError):sa.validate_fixture(blob(f))
        f = demo(); f['tables'][0]['columns'][0]['type'] = 'INTEGER); DROP TABLE public.users; --'
        with self.assertRaisesRegex(sa.AccuracyError, 'INVALID_FIXTURE_COLUMN'):
            sa.validate_fixture(blob(f))

    def test_duplicate_identifiers_casefold(self):
        f=demo(); f['tables'].append(copy.deepcopy(f['tables'][0])); f['tables'][1]['name']='queue'
        with self.assertRaisesRegex(sa.AccuracyError,'DUPLICATE_FIXTURE_TABLE'):
            sa.validate_fixture(blob(f))

    def test_reject_wrong_width_and_nonfinite(self):
        f=demo(); f['tables'][0]['rows'].append([1])
        with self.assertRaisesRegex(sa.AccuracyError,'INVALID_FIXTURE_ROW_WIDTH'):
            sa.validate_fixture(blob(f))
        f=demo(); f['tables'][0]['rows'][0][2]=float('nan')
        with self.assertRaisesRegex(sa.AccuracyError,'INVALID_FIXTURE_JSON'):
            sa.validate_fixture(blob(f))

    def test_expected_sort_is_multiset_including_duplicates(self):
        f=demo(); f['expected']['rows']=[['Alex'],['Alex'],['John']]
        self.assertEqual(sa.compare_result(f,['person_name'],[['John'],['Alex'],['Alex']]),(True,'PASS'))
        self.assertEqual(sa.compare_result(f,['person_name'],[['John'],['Alex']]),(False,'ROWS_MISMATCH'))

    def test_order_sensitive_is_explicit(self):
        f=demo(); f['expected']['order_sensitive']=True
        f['expected']['rows']=[['A'],['B']]
        self.assertEqual(sa.compare_result(f,['person_name'],[['B'],['A']]),(False,'ROWS_MISMATCH'))
        self.assertEqual(sa.compare_result(f,['person_name'],[['A'],['B']]),(True,'PASS'))

    def test_null_and_false_are_distinct(self):
        f=demo(); f['expected']['rows']=[[None]]
        self.assertTrue(sa.compare_result(f,['person_name'],[[None]])[0])
        self.assertFalse(sa.compare_result(f,['person_name'],[['']])[0])
        f['expected']['rows']=[[False]]
        self.assertTrue(sa.compare_result(f,['person_name'],[['f']])[0])

    def test_result_column_contract_enforced(self):
        f=demo()
        self.assertEqual(sa.compare_result(f,['name'],[['Alex']]),(False,'COLUMN_NAMES_MISMATCH'))
        self.assertEqual(sa.compare_result(f,['person_name','id'],[['Alex',2]]),(False,'COLUMN_COUNT_MISMATCH'))

    def test_reject_multiple_sql_statements_and_meta_commands(self):
        for sql in ('SELECT 1; DROP TABLE Queue;', 'DELETE FROM Queue',
                    'WITH stuff AS (SELECT 1) SELECT 1; SELECT 2',
                    'SELECT pg_sleep(999)', '\\! echo test', 'SELECT set_config(\'statement_timeout\',\'0\',true)'):
            with self.subTest(sql=sql),self.assertRaises(sa.AccuracyError):
                sa.validate_solution(sql)
        self.assertEqual(sa.validate_solution(' SELECT person_name FROM Queue; '),
                         'SELECT person_name FROM Queue')

    def test_bootstrap_uses_literal_escaping_and_low_privilege(self):
        f=demo(); f['tables'][0]['rows'][0][1]="O'Brien"
        script=sa.bootstrap_sql(f)
        self.assertIn("'O''Brien'",script)
        self.assertIn('NOSUPERUSER NOCREATEDB NOCREATEROLE',script)
        self.assertIn('GRANT SELECT ON ALL TABLES IN SCHEMA tia_fixture',script)
        self.assertIn('default_transaction_read_only TO on',script)
        self.assertNotIn('DROP DATABASE',script)

    def test_human_digest_is_required_before_process_launch(self):
        f=blob(demo())
        with patch.object(sa,'_postgres_run') as backend:
            with self.assertRaisesRegex(sa.AccuracyError,'HUMAN_FIXTURE_APPROVAL_REQUIRED'):
                sa.grade_fixture(f,'SELECT person_name FROM Queue','b'*64)
            backend.assert_not_called()

    def test_verified_result_is_only_from_real_backend_not_ai(self):
        f=blob(demo());digest=sa.validate_fixture(f)[1]
        with patch.object(sa,'_postgres_run',return_value={
              'status':'PASSED','reason':'PASS','actual_row_count':1,'expected_row_count':1}) as backend:
            report=sa.grade_fixture(f,'SELECT person_name FROM Queue',digest)
            self.assertEqual(report['correctness'],'VERIFIED_LOCAL_FIXTURE')
            self.assertEqual(report['passed_fixtures'],1)
            self.assertFalse(report['official_hidden_tests'])
            backend.assert_called_once()
        with patch.object(sa,'_postgres_run',return_value={
              'status':'EXECUTION_ERROR','error_code':'POSTGRES_QUERY_ERROR',
              'columns':None,'rows':None}):
            report=sa.grade_fixture(f,'SELECT person_name FROM Queue',digest)
            self.assertEqual(report['correctness'],'VERIFIED_LOCAL_FIXTURE')
            self.assertEqual(report['passed_fixtures'],0)

    def test_missing_server_never_connects_external_db(self):
        with patch('shutil.which',return_value=None):
            with self.assertRaisesRegex(sa.AccuracyError,'POSTGRES_SERVER_NOT_AVAILABLE'):
                sa._postgres_bins()
        with patch.dict('os.environ',{'PGHOST':'remote.example.org','PGPASSWORD':'secret',
                                      'PGOPTIONS':'-c search_path=public'},clear=False):
            env=sa._pg_environment()
            self.assertNotIn('PGHOST',env)
            self.assertNotIn('PGPASSWORD',env)
            self.assertNotIn('PGOPTIONS',env)

    def test_sample_inspection_cli_makes_no_database_calls(self):
        from pathlib import Path
        import subprocess,sys
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fixture.json';path.write_bytes(blob(demo()))
            cli=Path(__file__).resolve().parents[1]/'scripts'/'run_sql_accuracy.py'
            r=subprocess.run([sys.executable,str(cli),'--fixture',str(path)],
                             capture_output=True,text=True,timeout=6)
            self.assertEqual(r.returncode,0,r.stderr)
            result=json.loads(r.stdout)
            self.assertEqual(result['status'],'AWAITING_HUMAN_DIGEST_APPROVAL')
            self.assertFalse(result['executable'])


if __name__=='__main__':
    unittest.main()
