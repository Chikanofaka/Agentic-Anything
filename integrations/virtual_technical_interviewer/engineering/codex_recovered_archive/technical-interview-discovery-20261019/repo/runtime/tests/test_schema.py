"""Strict package-schema regressions and explicit, non-mutating legacy migration."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from hal_core.contracts import ContractError, inspect


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'fixtures/research'
RETURNS = ROOT / 'fixtures/returns'


class PackageSchemaTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.serial = 0

    def package(self, edit=None, *, legacy=False):
        self.serial += 1
        package = self.base / ('package-' + str(self.serial))
        shutil.copytree(RESEARCH, package)
        inspection = inspect(RESEARCH)
        manifest = copy.deepcopy(inspection.manifest if legacy else inspection.contract)
        if edit:
            edit(manifest)
        (package / 'harness.json').write_text(json.dumps(manifest), encoding='utf-8')
        return package

    def rejected(self, package, diagnostic):
        with self.assertRaises(ContractError) as caught:
            inspect(package)
        self.assertEqual(str(caught.exception), diagnostic)

    def test_unsupported_and_missing_schema_versions_fail_closed(self):
        for version in ('hal-domain/v2', 'hal-demo/v0.1', '', 1, True, None, []):
            with self.subTest(version=version):
                self.rejected(self.package(lambda m: m.update(schema_version=version)),
                              'UNSUPPORTED_SCHEMA')
        self.rejected(self.package(lambda m: m.pop('schema_version')), 'UNSUPPORTED_SCHEMA')

    def test_nonobject_manifest_is_rejected(self):
        for manifest in ([], 'manifest', 42, True, None):
            with self.subTest(manifest=manifest):
                package = self.package()
                (package / 'harness.json').write_text(json.dumps(manifest), encoding='utf-8')
                self.rejected(package, 'MANIFEST_NOT_OBJECT')

    def test_unsupported_or_malformed_host_is_rejected(self):
        for host in ({'api': 'hal-core/v2'}, {'api': 'hal-core/v1', 'extra': True},
                     {'api': 1}, {}, 'hal-core/v1', [], None):
            with self.subTest(host=host):
                self.rejected(self.package(lambda m: m.update(host=host)), 'UNSUPPORTED_HOST_API')

    def test_unknown_top_level_and_nested_fields_are_rejected(self):
        edits = {
            'top': lambda m: m.update(extra=True),
            'tool': lambda m: m['tools'][0].update(command='arbitrary-source'),
            'feature': lambda m: m['features'][0].update(command='arbitrary-source'),
            'capability': lambda m: m['features'][0]['required_capabilities'][0].update(extra=True),
        }
        for location, edit in edits.items():
            with self.subTest(location=location):
                self.rejected(self.package(edit), 'UNKNOWN_MANIFEST_FIELD')

    def test_missing_required_v1_fields_are_rejected(self):
        for field in ('id', 'name', 'version', 'domain', 'entrypoint', 'readme',
                      'skills', 'features', 'permissions', 'agents', 'host', 'tools'):
            with self.subTest(field=field):
                self.rejected(self.package(lambda m: m.pop(field)), 'MISSING_MANIFEST_FIELD')

    def test_missing_nested_fields_are_rejected(self):
        edits = {
            'tool input contract': lambda m: m['tools'][0].pop('input_contract'),
            'tool permissions': lambda m: m['tools'][0].pop('permissions'),
            'feature tool': lambda m: m['features'][0].pop('tool'),
            'feature permissions': lambda m: m['features'][0].pop('permissions'),
            'requirement capabilities': lambda m: m['features'][0]['required_capabilities'][0].pop('capabilities'),
        }
        for location, edit in edits.items():
            with self.subTest(location=location):
                self.rejected(self.package(edit), 'MISSING_MANIFEST_FIELD')

    def test_nested_objects_do_not_accept_scalar_or_list_types(self):
        edits = {
            'tool': lambda m, value: m['tools'].__setitem__(0, value),
            'feature': lambda m, value: m['features'].__setitem__(0, value),
            'requirement': lambda m, value: m['features'][0]['required_capabilities'].__setitem__(0, value),
        }
        for location, edit in edits.items():
            for value in (None, True, 'object', []):
                with self.subTest(location=location, value=value):
                    self.rejected(self.package(lambda m: edit(m, value)), 'EXPECTED_OBJECT')

    def test_lists_do_not_accept_objects_or_strings(self):
        edits = {
            'skills': lambda m, value: m.update(skills=value),
            'tools': lambda m, value: m.update(tools=value),
            'features': lambda m, value: m.update(features=value),
            'tool permissions': lambda m, value: m['tools'][0].update(permissions=value),
            'feature permissions': lambda m, value: m['features'][0].update(permissions=value),
            'requirements': lambda m, value: m['features'][0].update(required_capabilities=value),
            'capabilities': lambda m, value: m['features'][0]['required_capabilities'][0].update(capabilities=value),
        }
        for location, edit in edits.items():
            for value in (None, {}, 'calculate'):
                with self.subTest(location=location, value=value):
                    self.rejected(self.package(lambda m: edit(m, value)), 'INVALID_MANIFEST_LIST')

    def test_required_lists_cannot_be_empty(self):
        for field in ('skills', 'tools', 'features'):
            with self.subTest(field=field):
                self.rejected(self.package(lambda m: m.update({field: []})), 'INVALID_MANIFEST_LIST')
        self.rejected(self.package(lambda m: m['features'][0].update(required_capabilities=[])),
                      'INVALID_MANIFEST_LIST')

    def test_invalid_identifiers_and_contract_versions_are_rejected(self):
        edits = {
            'id': lambda m: m.update(id='../package'),
            'domain': lambda m: m.update(domain='Research'),
            'version': lambda m: m.update(version='01.0.0'),
            'tool id': lambda m: m['tools'][0].update(id='ab'),
            'feature id': lambda m: m['features'][0].update(id='feature with spaces'),
            'input contract': lambda m: m['tools'][0].update(input_contract='research-margin-input/v0'),
            'output contract': lambda m: m['tools'][0].update(output_contract='research-margin-output'),
        }
        for location, edit in edits.items():
            with self.subTest(location=location):
                self.rejected(self.package(edit), 'INVALID_MANIFEST_IDENTIFIER')

    def test_text_fields_do_not_coerce_invalid_values(self):
        for field in ('id', 'name', 'version', 'domain', 'description'):
            for value in (None, 1, True, [], {}, '', '   '):
                with self.subTest(field=field, value=value):
                    self.rejected(self.package(lambda m: m.update({field: value})),
                                  'INVALID_MANIFEST_STRING')

    def test_duplicate_tool_and_feature_ids_are_rejected(self):
        for field, diagnostic in (('tools', 'DUPLICATE_TOOL_ID'), ('features', 'DUPLICATE_FEATURE_ID')):
            with self.subTest(field=field):
                self.rejected(self.package(lambda m: m[field].append(copy.deepcopy(m[field][0]))), diagnostic)

    def test_duplicate_declarations_are_rejected(self):
        edits = {
            'skills': lambda m: m['skills'].append(m['skills'][0]),
            'tool permissions': lambda m: m['tools'][0].update(permissions=['network', 'network']),
            'feature permissions': lambda m: m['features'][0].update(permissions=['network', 'network']),
            'capabilities': lambda m: m['features'][0]['required_capabilities'][0].update(capabilities=['calculate', 'calculate']),
        }
        for location, edit in edits.items():
            with self.subTest(location=location):
                self.rejected(self.package(edit), 'DUPLICATE_DECLARATION')

    def test_duplicate_required_port_is_rejected(self):
        self.rejected(self.package(lambda m: m['features'][0]['required_capabilities'].append(
            {'port': 'LOCAL_CALCULATE', 'capabilities': []})), 'DUPLICATE_REQUIRED_PORT')

    def test_undeclared_and_nonstring_feature_tools_are_rejected(self):
        for tool in ('undeclared-tool', None, {}, 1):
            with self.subTest(tool=tool):
                self.rejected(self.package(lambda m: m['features'][0].update(tool=tool)), 'UNDECLARED_TOOL')

    def test_tool_port_must_appear_in_feature_requirements(self):
        self.rejected(self.package(lambda m: m['features'][0].update(required_capabilities=[
            {'port': 'LLM_DIRECT', 'capabilities': ['tool_calling']}])), 'TOOL_PORT_NOT_REQUIRED')

    def test_unknown_or_malformed_ports_are_rejected(self):
        for port in ('LOCAL_SHELL', None, [], 1):
            for location in ('tool', 'requirement'):
                with self.subTest(port=port, location=location):
                    def edit(manifest):
                        target = manifest['tools'][0] if location == 'tool' else manifest['features'][0]['required_capabilities'][0]
                        target['port'] = port
                    self.rejected(self.package(edit), 'UNKNOWN_PORT')

    def test_unknown_or_malformed_capabilities_and_permissions_are_rejected(self):
        edits = {
            'capability': lambda m, value: m['features'][0]['required_capabilities'][0].update(capabilities=[value]),
            'tool permission': lambda m, value: m['tools'][0].update(permissions=[value]),
            'feature permission': lambda m, value: m['features'][0].update(permissions=[value]),
        }
        for location, edit in edits.items():
            for value in ('arbitrary_execute', None, {}, True):
                with self.subTest(location=location, value=value):
                    self.rejected(self.package(lambda m: edit(m, value)), 'UNKNOWN_CAPABILITY_OR_PERMISSION')

    def test_all_referenced_assets_must_exist(self):
        for field in ('entrypoint', 'readme', 'agents'):
            with self.subTest(field=field):
                self.rejected(self.package(lambda m: m.update({field: 'missing.txt'})),
                              'MISSING_REQUIRED_FILE:' + field)
        self.rejected(self.package(lambda m: m.update(skills=['skills/missing/SKILL.md'])), 'MISSING_SKILL_FILE')

    def test_asset_references_must_be_strings_and_regular_files(self):
        for field in ('entrypoint', 'readme', 'agents'):
            for value in (None, [], {}, True, 'skills'):
                with self.subTest(field=field, value=value):
                    self.rejected(self.package(lambda m: m.update({field: value})), 'MISSING_REQUIRED_FILE:' + field)
        for value in (None, [], {}, True, 'skills'):
            with self.subTest(skill=value):
                self.rejected(self.package(lambda m: m.update(skills=[value])), 'MISSING_SKILL_FILE')

    def test_permission_policy_cannot_be_weakened_or_extended(self):
        for policy in ({'filesystem': 'all', 'external_write': 'approval_required'},
                       {'filesystem': 'selected_paths_only', 'external_write': 'always'},
                       {'filesystem': 'selected_paths_only', 'external_write': 'approval_required', 'network': 'allow'},
                       {}, [], None):
            with self.subTest(policy=policy):
                self.rejected(self.package(lambda m: m.update(permissions=policy)), 'UNSAFE_PERMISSION_DECLARATION')

    def test_legacy_normalization_preserves_source_bytes_and_content_digest(self):
        for fixture, tool_id, local_port, capability in (
            (RESEARCH, 'calculate-margin', 'LOCAL_CALCULATE', 'calculate'),
            (RETURNS, 'triage-return', 'LOCAL_TRIAGE', 'triage'),
        ):
            with self.subTest(domain=fixture.name):
                before = {p.relative_to(fixture).as_posix(): p.read_bytes()
                          for p in fixture.rglob('*') if p.is_file()}
                digest = hashlib.sha256()
                for name in sorted(before):
                    digest.update(name.encode('utf-8') + b'\0' + hashlib.sha256(before[name]).digest())
                inspection = inspect(fixture)
                self.assertEqual(inspection.digest, digest.hexdigest())
                self.assertEqual(inspection.manifest, json.loads(before['harness.json']))
                self.assertEqual(inspection.manifest['schema_version'], 'hal-demo/v0.2')
                self.assertEqual(inspection.contract['schema_version'], 'hal-domain/v1')
                self.assertIn('LEGACY_SCHEMA_NORMALIZED', inspection.warnings)
                self.assertEqual(inspection.contract['host'], {'api': 'hal-core/v1'})
                self.assertEqual(inspection.contract['agents'], 'AGENTS.md')
                self.assertNotIn('model_requirements', inspection.contract)
                self.assertEqual(inspection.contract['features'][0], {
                    'id': tool_id, 'tool': tool_id, 'permissions': [],
                    'required_capabilities': [{'port': local_port, 'capabilities': [capability]}],
                })
                self.assertEqual(inspection.contract['features'][1]['required_capabilities'], [
                    {'port': 'LLM_DIRECT', 'capabilities': ['tool_calling']},
                    {'port': local_port, 'capabilities': [capability]},
                ])
                after = {p.relative_to(fixture).as_posix(): p.read_bytes()
                         for p in fixture.rglob('*') if p.is_file()}
                self.assertEqual(after, before)

    def test_native_v1_inspection_has_no_legacy_migration_warning(self):
        inspection = inspect(self.package())
        self.assertEqual(inspection.manifest, inspection.contract)
        self.assertNotIn('LEGACY_SCHEMA_NORMALIZED', inspection.warnings)

    def test_legacy_unknown_fields_and_bad_model_requirements_are_rejected(self):
        self.rejected(self.package(lambda m: m.update(extra=True), legacy=True), 'UNKNOWN_MANIFEST_FIELD')
        for value in (None, [], True, 'tool_calling'):
            with self.subTest(value=value):
                self.rejected(self.package(lambda m: m.update(model_requirements=value), legacy=True), 'EXPECTED_OBJECT')
        self.rejected(self.package(lambda m: m.update(model_requirements={'unknown': True}), legacy=True),
                      'UNKNOWN_MANIFEST_FIELD')
        for value in (1, 0, 'true', [], None):
            with self.subTest(tool_calling=value):
                self.rejected(self.package(lambda m: m.update(model_requirements={'tool_calling': value}), legacy=True),
                              'INVALID_MODEL_REQUIREMENT')

    def test_legacy_model_requirement_false_or_omitted_is_explicit(self):
        edits = (lambda m: m.pop('model_requirements'),
                 lambda m: m.update(model_requirements={}),
                 lambda m: m.update(model_requirements={'tool_calling': False}))
        for edit in edits:
            inspection = inspect(self.package(edit, legacy=True))
            self.assertEqual(inspection.contract['features'][1]['required_capabilities'][0],
                             {'port': 'LLM_DIRECT', 'capabilities': []})

    def test_legacy_migration_requires_exactly_one_supported_local_port(self):
        for ports in ([], ['LLM_DIRECT'], ['LOCAL_CALCULATE', 'LOCAL_TRIAGE']):
            with self.subTest(ports=ports):
                self.rejected(self.package(lambda m: m['features'][0].update(required_ports=ports), legacy=True),
                              'LEGACY_MIGRATION_UNSUPPORTED')

    def test_legacy_duplicate_and_unknown_ports_are_rejected(self):
        self.rejected(self.package(lambda m: m['features'][0].update(required_ports=['LOCAL_CALCULATE'] * 2), legacy=True),
                      'DUPLICATE_DECLARATION')
        self.rejected(self.package(lambda m: m['features'][0].update(required_ports=['LOCAL_SHELL']), legacy=True),
                      'UNKNOWN_CAPABILITY_OR_PERMISSION')

    def test_legacy_migration_requires_agents_asset(self):
        package = self.package(legacy=True)
        (package / 'AGENTS.md').unlink()
        self.rejected(package, 'MISSING_REQUIRED_FILE:agents')

    def test_nonexistent_package_returns_static_diagnostic(self):
        self.rejected(self.base / 'NONEXISTENT_UNTRUSTED_PATH', 'PACKAGE_NOT_FOUND')


if __name__ == '__main__':
    unittest.main()
