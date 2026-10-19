"""Exercise the actual offline CLI process and its JSON/exit-code boundary."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNTIME = Path(__file__).resolve().parents[1]
RESEARCH = RUNTIME / 'fixtures/research'
RETURNS = RUNTIME / 'fixtures/returns'


class CliContractTests(unittest.TestCase):
    def cli(self, *arguments, expected_exit=0):
        completed = subprocess.run(
            [sys.executable, '-B', '-m', 'hal_core.cli', *map(str, arguments)],
            cwd=RUNTIME, capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(completed.returncode, expected_exit, completed.stdout + completed.stderr)
        self.assertEqual(completed.stderr, '')
        self.assertNotIn('Traceback', completed.stdout)
        output = json.loads(completed.stdout)
        # json.loads accepts NaN/Infinity by default; this explicitly rejects them.
        json.dumps(output, allow_nan=False)
        return output, completed.stdout

    def test_normalized_inspection_emits_v1_without_modifying_source(self):
        before = {p.relative_to(RESEARCH): p.read_bytes()
                  for p in RESEARCH.rglob('*') if p.is_file()}
        output, _ = self.cli('inspect', '--package', RESEARCH, '--normalized')
        self.assertEqual(output['schema_version'], 'hal-domain/v1')
        self.assertEqual(output['id'], 'research-diagnostics')
        self.assertEqual(output['host'], {'api': 'hal-core/v1'})
        self.assertEqual(output['tools'][0]['input_contract'], 'research-margin-input/v1')
        after = {p.relative_to(RESEARCH): p.read_bytes()
                 for p in RESEARCH.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(json.loads(after[Path('harness.json')])['schema_version'], 'hal-demo/v0.2')

    def test_research_golden_run_has_finite_json_receipt(self):
        output, _ = self.cli('run', '--package', RESEARCH, '--feature', 'calculate-margin',
                             '--payload', '{"revenue":1500,"cost":900}')
        self.assertEqual(output['status'], 'SUCCESS')
        self.assertEqual(output['result']['profit'], 600)
        self.assertEqual(output['result']['margin_pct'], 40)
        self.assertFalse(output['live_model_used'])
        self.assertFalse(output['external_writes'])

    def test_returns_golden_run_has_finite_json_receipt(self):
        output, _ = self.cli('run', '--package', RETURNS, '--feature', 'triage-return',
                             '--payload', '{"condition":"sealed","proof":"yes","days":5}')
        self.assertEqual(output['status'], 'SUCCESS')
        self.assertEqual(output['result']['classification'], 'STANDARD_RETURN')
        self.assertFalse(output['live_model_used'])
        self.assertFalse(output['external_writes'])

    def test_malformed_payload_is_static_json_error(self):
        output, stdout = self.cli('run', '--package', RESEARCH, '--feature', 'calculate-margin',
                                  '--payload', '{"PRIVATE_SENTINEL":', expected_exit=2)
        self.assertEqual(output, {'status': 'ERROR', 'reason': 'INVALID_JSON'})
        self.assertNotIn('PRIVATE_SENTINEL', stdout)

    def test_duplicate_payload_key_is_static_json_error(self):
        output, stdout = self.cli('run', '--package', RESEARCH, '--feature', 'calculate-margin',
                                  '--payload', '{"revenue":1,"revenue":2,"cost":"PRIVATE_SENTINEL"}',
                                  expected_exit=2)
        self.assertEqual(output, {'status': 'ERROR', 'reason': 'DUPLICATE_JSON_KEY'})
        self.assertNotIn('PRIVATE_SENTINEL', stdout)

    def test_nonfinite_payload_numbers_are_static_json_errors(self):
        for number in ('NaN', 'Infinity', '-Infinity', '1e999'):
            with self.subTest(number=number):
                payload = '{"revenue":' + number + ',"cost":1,"extra":"PRIVATE_SENTINEL"}'
                output, stdout = self.cli('run', '--package', RESEARCH, '--feature', 'calculate-margin',
                                          '--payload', payload, expected_exit=2)
                self.assertEqual(output, {'status': 'ERROR', 'reason': 'NON_FINITE_JSON'})
                self.assertNotIn('PRIVATE_SENTINEL', stdout)

    def test_oversized_integer_payload_is_static_json_error(self):
        payload = '{"revenue":' + ('9' * 1025) + ',"cost":1,"extra":"PRIVATE_SENTINEL"}'
        output, stdout = self.cli('run', '--package', RESEARCH, '--feature', 'calculate-margin',
                                  '--payload', payload, expected_exit=2)
        self.assertEqual(output, {'status': 'ERROR', 'reason': 'JSON_NUMBER_TOO_LARGE'})
        self.assertNotIn('PRIVATE_SENTINEL', stdout)

    def test_malformed_zip_inspection_and_run_are_structured_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'PRIVATE_SENTINEL.zip'
            package.write_bytes(b'PK\x03\x04PRIVATE_SENTINEL')
            for action in ('inspect', 'run'):
                with self.subTest(action=action):
                    arguments = [action, '--package', package]
                    if action == 'run':
                        arguments.extend(['--feature', 'calculate-margin', '--payload', '{"revenue":10,"cost":1}'])
                    output, stdout = self.cli(*arguments, expected_exit=2)
                    self.assertEqual(output['reason'], 'INVALID_ZIP')
                    self.assertEqual(output['status'], 'ERROR' if action == 'inspect' else 'BLOCKED')
                    self.assertNotIn('result', output)
                    self.assertNotIn('PRIVATE_SENTINEL', stdout)

    def test_managed_agent_denial_preserves_local_capability_evidence(self):
        output, _ = self.cli('preflight', '--package', RESEARCH, '--feature', 'ai-interpretation',
                             '--provider', 'manus', expected_exit=2)
        self.assertEqual(output['status'], 'BLOCKED')
        self.assertEqual(output['missing_ports'], ['MANAGED_AGENT_PORT_MISMATCH'])
        self.assertEqual(output['missing_permissions'], [])
        self.assertEqual(output['checks'][0]['tool'], 'calculate-margin')
        self.assertEqual(output['checks'][0]['state'], 'AVAILABLE_CURATED_LOCAL')
        self.assertFalse(output['live_model_verified'])


if __name__ == '__main__':
    unittest.main()
