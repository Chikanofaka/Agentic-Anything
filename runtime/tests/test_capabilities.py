"""Contract-to-host integration, effect denials and numeric/output regressions."""
from dataclasses import replace
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

from hal_core.contracts import inspect
from hal_core.engine import run
from hal_core.ports import feature_status
from hal_core.registry import Port, TRUSTED

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'fixtures/research'
RETURNS = ROOT / 'fixtures/returns'


class CapabilityContractTests(unittest.TestCase):
    def package(self, domain='research', edit=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        package = Path(temporary.name) / 'package'
        shutil.copytree(ROOT / 'fixtures' / domain, package)
        manifest = json.loads((package / 'harness.json').read_text())
        manifest.pop('model_requirements', None)
        manifest.update(schema_version='hal-domain/v1', version='1.0.0',
                        agents='AGENTS.md', host={'api': 'hal-core/v1'})
        research = domain == 'research'
        tool_id = 'calculate-margin' if research else 'triage-return'
        port = 'LOCAL_CALCULATE' if research else 'LOCAL_TRIAGE'
        capability = 'calculate' if research else 'triage'
        prefix = 'research-margin' if research else 'returns-triage'
        manifest['tools'] = [{
            'id': tool_id, 'port': port, 'input_contract': prefix + '-input/v1',
            'output_contract': prefix + '-output/v1', 'permissions': [],
        }]
        manifest['features'] = [{
            'id': tool_id, 'tool': tool_id, 'permissions': [],
            'required_capabilities': [{'port': port, 'capabilities': [capability]}],
        }, {
            'id': 'ai-interpretation', 'tool': tool_id, 'permissions': [],
            'required_capabilities': [
                {'port': 'LLM_DIRECT', 'capabilities': ['tool_calling']},
                {'port': port, 'capabilities': [capability]},
            ],
        }]
        if edit:
            edit(manifest)
        (package / 'harness.json').write_text(json.dumps(manifest))
        return package

    def assert_blocked(self, receipt):
        self.assertEqual(receipt['status'], 'BLOCKED')
        self.assertNotIn('result', receipt)
        self.assertFalse(receipt['live_model_used'])
        self.assertFalse(receipt['external_writes'])
        json.dumps(receipt, allow_nan=False)

    def test_v1_research_golden_and_typed_receipt(self):
        result = run(self.package(), 'calculate-margin', {'revenue': 1500, 'cost': 900})
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['result']['profit'], 600)
        self.assertEqual(result['result']['margin_pct'], 40)
        self.assertEqual(result['contract_schema'], 'hal-domain/v1')
        self.assertEqual(result['input_contract'], 'research-margin-input/v1')
        self.assertEqual(result['permissions'], [])
        self.assertIn({'code': 'OUTPUT_VALIDATED'}, result['events'])

    def test_v1_returns_golden(self):
        result = run(self.package('returns'), 'triage-return',
                     {'condition': 'sealed', 'proof': 'yes', 'days': 5})
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['result']['classification'], 'STANDARD_RETURN')

    def test_registry_ports_are_typed(self):
        self.assertIs(TRUSTED[('research-diagnostics', 'calculate-margin')].port, Port.LOCAL_CALCULATE)

    def test_legacy_ai_feature_has_available_local_tool(self):
        status = feature_status(inspect(RESEARCH), 'ai-interpretation', 'openai')
        self.assertEqual(status['status'], 'BLOCKED')
        self.assertEqual(status['missing_ports'], ['LLM_DIRECT:UNVERIFIED_LIVE_CREDENTIALS_AND_CAPABILITIES'])
        self.assertEqual(status['checks'][0]['tool'], 'calculate-margin')
        self.assertFalse(status['live_model_verified'])

    def test_new_feature_reuses_registered_tool(self):
        package = self.package(edit=lambda m: m['features'][0].update(id='margin-preview'))
        result = run(package, 'margin-preview', {'revenue': 100, 'cost': 25})
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['result']['margin_pct'], 75)

    def test_tool_port_mismatch_blocks(self):
        package = self.package(edit=lambda m: m['tools'][0].update(port='LOCAL_TRIAGE'))
        self.assert_blocked(run(package, 'calculate-margin', {'revenue': 10, 'cost': 1}))

    def test_input_contract_mismatch_blocks(self):
        package = self.package(edit=lambda m: m['tools'][0].update(input_contract='returns-triage-input/v1'))
        status = feature_status(inspect(package), 'calculate-margin')
        self.assertIn('LOCAL_CALCULATE:TOOL_CONTRACT_MISMATCH', status['missing_ports'])
        self.assertFalse(status['tool_contract_verified'])
        self.assert_blocked(run(package, 'calculate-margin', {'revenue': 10, 'cost': 1}))

    def test_output_contract_mismatch_blocks(self):
        package = self.package(edit=lambda m: m['tools'][0].update(output_contract='returns-triage-output/v1'))
        self.assert_blocked(run(package, 'calculate-margin', {'revenue': 10, 'cost': 1}))

    def test_unknown_contract_is_inspectable_but_not_executable(self):
        package = self.package(edit=lambda m: m['tools'][0].update(input_contract='unknown-input/v1'))
        self.assertEqual(inspect(package).contract['tools'][0]['input_contract'], 'unknown-input/v1')
        self.assert_blocked(run(package, 'calculate-margin', {'revenue': 10, 'cost': 1}))

    def test_unknown_tool_is_inspectable_but_not_executable(self):
        def edit(manifest):
            manifest['tools'][0]['id'] = 'unreviewed-tool'
            for feature in manifest['features']:
                feature['tool'] = 'unreviewed-tool'
        package = self.package(edit=edit)
        status = feature_status(inspect(package), 'calculate-margin')
        self.assertIn('LOCAL_CALCULATE:NO_CURATED_BINDING', status['missing_ports'])
        self.assert_blocked(run(package, 'calculate-margin', {'revenue': 10, 'cost': 1}))

    def test_feature_permission_requests_never_grant_effects(self):
        original = TRUSTED[('research-diagnostics', 'calculate-margin')]
        handler = Mock(wraps=original.handler)
        with patch.dict(TRUSTED, {('research-diagnostics', 'calculate-margin'): replace(original, handler=handler)}):
            for permission in ('selected_files_read', 'network', 'external_write'):
                with self.subTest(permission=permission):
                    package = self.package(edit=lambda m: m['features'][0].update(permissions=[permission]))
                    status = feature_status(inspect(package), 'calculate-margin')
                    self.assertEqual(status['missing_permissions'], [permission])
                    self.assertEqual(status['missing_ports'], [])
                    self.assert_blocked(run(package, 'calculate-margin', {'revenue': 10, 'cost': 1}))
            handler.assert_not_called()

    def test_tool_permission_request_mismatches_host_contract(self):
        package = self.package(edit=lambda m: m['tools'][0].update(permissions=['external_write']))
        status = feature_status(inspect(package), 'calculate-margin')
        self.assertEqual(status['missing_permissions'], ['external_write'])
        self.assertIn('LOCAL_CALCULATE:TOOL_CONTRACT_MISMATCH', status['missing_ports'])
        self.assert_blocked(run(package, 'calculate-margin', {'revenue': 10, 'cost': 1}))

    def test_unimplemented_local_capability_blocks(self):
        package = self.package(edit=lambda m: m['features'][0]['required_capabilities'][0].update(capabilities=['structured_output']))
        status = feature_status(inspect(package), 'calculate-margin')
        self.assertIn('LOCAL_CALCULATE:MISSING_CAPABILITY:structured_output', status['missing_ports'])
        self.assert_blocked(run(package, 'calculate-margin', {'revenue': 10, 'cost': 1}))

    def test_unimplemented_port_families_block(self):
        for port in ('MANAGED_AGENT', 'EMBEDDED_CHANNEL', 'DATA_FEED', 'TOOL_API'):
            with self.subTest(port=port):
                package = self.package(edit=lambda m: m['features'][0]['required_capabilities'].append({'port': port, 'capabilities': []}))
                status = feature_status(inspect(package), 'calculate-margin')
                self.assertIn(port + ':NO_REGISTERED_ADAPTER', status['missing_ports'])
                self.assert_blocked(run(package, 'calculate-margin', {'revenue': 10, 'cost': 1}))

    def test_v1_managed_agent_cannot_activate_direct_model(self):
        status = feature_status(inspect(self.package()), 'ai-interpretation', 'manus')
        self.assertEqual(status['missing_ports'], ['MANAGED_AGENT_PORT_MISMATCH'])
        self.assertEqual(status['checks'][0]['port'], 'LOCAL_CALCULATE')
        self.assertFalse(status['live_model_verified'])

    def test_unknown_feature_returns_complete_blocked_status(self):
        status = feature_status(inspect(RESEARCH), 'unknown-feature')
        self.assertEqual(status['reason'], 'UNKNOWN_FEATURE')
        self.assertEqual(status['missing_permissions'], [])
        self.assert_blocked(run(RESEARCH, 'unknown-feature', {'revenue': 10, 'cost': 1}))

    def test_huge_integer_is_blocked_without_crash(self):
        self.assert_blocked(run(RESEARCH, 'calculate-margin', {'revenue': 10**1000, 'cost': 900}))

    def test_finite_inputs_cannot_produce_infinite_success_output(self):
        receipt = run(RESEARCH, 'calculate-margin', {'revenue': 1e-308, 'cost': 1e308})
        self.assert_blocked(receipt)
        self.assertEqual(receipt['reason'], 'VALUE_CONTRACT_NON_FINITE_NUMBER')
        self.assertIn({'code': 'TRUSTED_TOOL_EXECUTED'}, receipt['events'])
        self.assertNotIn({'code': 'OUTPUT_VALIDATED'}, receipt['events'])

    def test_nonfinite_and_boolean_numeric_inputs_block_before_tool(self):
        original = TRUSTED[('research-diagnostics', 'calculate-margin')]
        handler = Mock(wraps=original.handler)
        with patch.dict(TRUSTED, {('research-diagnostics', 'calculate-margin'): replace(original, handler=handler)}):
            for invalid in (float('nan'), float('inf'), float('-inf'), True, '100'):
                with self.subTest(invalid=invalid):
                    self.assert_blocked(run(RESEARCH, 'calculate-margin', {'revenue': invalid, 'cost': 1}))
            handler.assert_not_called()

    def test_unexpected_adapter_output_never_becomes_result(self):
        original = TRUSTED[('research-diagnostics', 'calculate-margin')]
        invalid_results = [None, {'profit': 1}, {'profit': 1, 'margin_pct': 1,
                           'unit': 'user_supplied_units', 'rule': 'wrong-rule'}]
        for invalid in invalid_results:
            with self.subTest(output=invalid), patch.dict(TRUSTED, {
                    ('research-diagnostics', 'calculate-margin'): replace(original, handler=lambda payload: invalid)}):
                self.assert_blocked(run(RESEARCH, 'calculate-margin', {'revenue': 10, 'cost': 1}))

    def test_adapter_exception_text_is_not_in_receipt(self):
        original = TRUSTED[('research-diagnostics', 'calculate-margin')]
        handler = Mock(side_effect=RuntimeError('PRIVATE_SENTINEL'))
        with patch.dict(TRUSTED, {('research-diagnostics', 'calculate-margin'): replace(original, handler=handler)}):
            receipt = run(RESEARCH, 'calculate-margin', {'revenue': 10, 'cost': 1})
        self.assert_blocked(receipt)
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(receipt))
        self.assertEqual(receipt['reason'], 'TRUSTED_TOOL_EXECUTION_FAILED')

    def test_nested_secret_payload_not_echoed(self):
        receipt = run(RESEARCH, 'calculate-margin', {'revenue': {'secret': 'PRIVATE_SENTINEL'}, 'cost': 1})
        self.assert_blocked(receipt)
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(receipt))

    def test_boolean_budget_does_not_count_as_one_tool_call(self):
        self.assert_blocked(run(RESEARCH, 'calculate-margin', {'revenue': 10, 'cost': 1}, max_tool_calls=True))

    def test_returns_boolean_days_are_rejected(self):
        self.assert_blocked(run(RETURNS, 'triage-return', {'condition': 'sealed', 'proof': 'yes', 'days': True}))


if __name__ == '__main__':
    unittest.main()
