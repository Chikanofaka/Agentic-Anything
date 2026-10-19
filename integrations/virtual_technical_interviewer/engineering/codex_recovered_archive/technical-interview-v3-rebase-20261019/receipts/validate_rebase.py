"""Validate document/source consistency; this does not run TIA application acceptance."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OLD = Path('[LOCAL_PATH_REDACTED]')
SOURCES = ROOT / 'sources/TIA_FULL_PRD_v3'
PREFIX = 'integrations/virtual_technical_interviewer/TIA_FULL_PRD_v3/'
SHA = '53188034400be6c534d2ded56a9386ea55d6ad0e'
checks = []
warnings = []


def load(path):
    return json.loads(path.read_text())


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def check(name, passed, detail):
    checks.append({'check': name, 'status': 'PASS' if passed else 'FAIL', 'detail': detail})


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


remote = load(ROOT / 'receipts/remote_manifest.json')
remote_files = {x['path']: x for x in remote['files']}
prior = load(OLD / 'receipts/canonical_manifest.json')
prior_files = {x['path']: x for x in prior['files']}
check('pinned_source_revision', remote['commit'] == SHA, remote['commit'])

verified = []
for path in sorted(SOURCES.iterdir()):
    record = remote_files[PREFIX + path.name]
    data = path.read_bytes()
    verified.append({'file': path.name, 'git_blob_match': blob(data) == record['sha'],
                     'bytes_match': len(data) == record['size'],
                     'sha256': hashlib.sha256(data).hexdigest()})
check('ten_text_sources_match_pinned_git_blobs', len(verified) == 10 and all(
    x['git_blob_match'] and x['bytes_match'] for x in verified), verified)

manifest = load(SOURCES / 'SHA256_MANIFEST.json')
manifest_texts = []
for entry in manifest['files']:
    path = SOURCES / entry['file']
    if path.exists():
        data = path.read_bytes()
        manifest_texts.append({'file': path.name, 'match': len(data) == entry['bytes'] and
                               hashlib.sha256(data).hexdigest() == entry['sha256']})
    else:
        actual = remote_files[PREFIX + entry['file']]
        warnings.append({'type': 'BINARY_NOT_DOWNLOADED_OR_CONTENT_VERIFIED', 'file': entry['file'],
                         'manifest_bytes': entry['bytes'], 'git_tree_bytes': actual['size'],
                         'metadata_size_match': entry['bytes'] == actual['size']})
check('eight_manifest_covered_text_files_match', len(manifest_texts) == 8 and
      all(x['match'] for x in manifest_texts), manifest_texts)

added = sorted(set(remote_files) - set(prior_files))
removed = sorted(set(prior_files) - set(remote_files))
modified = sorted(p for p in set(remote_files) & set(prior_files)
                  if remote_files[p]['sha'] != prior_files[p]['sha'])
check('tree_delta_has_no_modified_existing_files', not modified and len(added) == 12 and len(removed) == 1,
      {'added': added, 'removed': removed, 'modified': modified})

code = [p for p in remote_files if p.startswith(('runtime/', 'scripts/', 'integrations/witness_loop/native/'))
        or p == 'AGENTS.md']
mismatches = [p for p in code if not (OLD / 'repo' / p).is_file()
              or blob((OLD / 'repo' / p).read_bytes()) != remote_files[p]['sha']]
check('audited_runtime_native_scripts_unchanged', not mismatches, {'count': len(code), 'mismatches': mismatches})

trace = rows(ROOT / 'REBASED_SOURCE_TRACEABILITY.csv')
tests = rows(ROOT / 'ACCEPTANCE_TEST_MATRIX_V3.csv')
trace_ids = {x['canonical_id'] for x in trace}
expected_fr = {f'v3:FR-{i:02}' for i in range(1, 29)}
expected_com = {f'v3:COM-FR-{i:03}' for i in range(1, 13)}
check('trace_all_28_fr_and_12_com', expected_fr | expected_com <= trace_ids,
      {'missing': sorted((expected_fr | expected_com) - trace_ids), 'rows': len(trace)})
check('trace_ids_unique', len({x['trace_id'] for x in trace}) == len(trace), len(trace))
legacy_trace = {x['mapping_id'] for x in rows(OLD / 'SOURCE_TO_GRAPH_TO_REQUIREMENT.csv')}
referenced_legacy = set(re.findall(r'legacy:([A-Z]+-?\d+)', '\n'.join(x['legacy_trace_ids'] for x in trace)))
check('all_old_trace_rows_reconciled', legacy_trace <= referenced_legacy,
      {'old_count': len(legacy_trace), 'missing': sorted(legacy_trace - referenced_legacy)})

legacy_tests = {x['test_id'] for x in rows(OLD / 'ACCEPTANCE_TEST_MATRIX.csv')}
retained_tests = {x['legacy_test_id'] for x in tests if x['legacy_test_id']}
check('all_84_old_cases_reconciled', legacy_tests == retained_tests,
      {'old_count': len(legacy_tests), 'missing': sorted(legacy_tests - retained_tests)})
check('new_acceptance_statuses_are_honest', all(x['status'] == 'NOT_RUN' and not x['actual_result'] and
      not x['evidence_ref'] for x in tests), {'rows': len(tests), 'statuses': dict(Counter(x['status'] for x in tests))})
check('new_test_ids_unique', len({x['test_id'] for x in tests}) == len(tests), len(tests))
test_ids = {x['test_id'] for x in tests}
missing_links = []
unresolved_links = []
for row in trace:
    linked = {s.strip() for s in row.get('acceptance_test_ids', '').split(';')
              if s.strip() and s.strip() not in ('NONE', 'NO_EXPLICIT_TEST_JOIN')}
    if row['row_kind'] in ('FUNCTIONAL_REQUIREMENT', 'COMMUNICATION_REQUIREMENT') and not linked:
        missing_links.append(row['canonical_id'])
    for ref in linked:
        if ref not in test_ids:
            unresolved_links.append({'trace': row['trace_id'], 'test': ref})
check('trace_to_planned_acceptance_links_resolve', not missing_links and not unresolved_links,
      {'requirements_without_test_link': missing_links, 'unresolved_links': unresolved_links})
unmapped_test_rows = [x['canonical_id'] for x in trace
                      if x.get('acceptance_test_ids') == 'NO_EXPLICIT_TEST_JOIN']
if unmapped_test_rows:
    warnings.append({'type': 'TRACE_ROWS_WITH_NO_EXPLICIT_TEST_JOIN', 'rows': unmapped_test_rows})
expected_uat = {f'C-UAT-{i:02}' for i in range(1, 13)} | {f'INT-UAT-{i:02}' for i in range(1, 6)}
mapped_uat = set(re.findall(r'(?:C|INT)-UAT-\d{2}', '\n'.join(x['v3_uat_ids'] for x in tests)))
check('all_17_supplied_uat_planned', expected_uat <= mapped_uat, {'missing': sorted(expected_uat - mapped_uat)})
test_text = '\n'.join(';'.join(x.values()) for x in tests)
expected_hs = {f'PRD28-HS-{i:02}' for i in range(1, 13)}
check('twelve_hard_stop_scenarios_planned', all(x in test_text for x in expected_hs),
      {'missing': sorted(x for x in expected_hs if x not in test_text)})
check('all_12_com_have_planned_cases', all(x[3:] in test_text for x in expected_com),
      {'missing': sorted(x for x in expected_com if x[3:] not in test_text)})
exam_text = ';'.join(x['communication_exam_ids'] for x in tests)
expected_exam = {f'exam:C{i:02}' for i in range(1, 17)}
check('all_16_exam_observations_planned', all(x in exam_text for x in expected_exam),
      {'missing': sorted(x for x in expected_exam if x not in exam_text)})
m0 = {f'FR-{i:02}' for i in range(1, 15)} | {'FR-25', 'FR-27', 'FR-28'}
missing_polarity = []
for req in sorted(m0):
    relevant = [r for r in tests if req in r['requirement_ids'].split(';')]
    for polarity in ['positive', 'negative']:
        if not any(r['polarity'] == polarity for r in relevant):
            missing_polarity.append(f'{req}:{polarity}')
check('each_m0_requirement_has_positive_and_negative_plan', not missing_polarity, missing_polarity)
check('each_case_has_expected_and_failure_conditions', all(x['expected_result'].strip() and
      x['failure_condition'].strip() for x in tests),
      [x['test_id'] for x in tests if not x['expected_result'].strip() or not x['failure_condition'].strip()])
check('each_case_has_verification_and_evidence_plan', all(x.get('verification_method', '').strip() and
      x.get('required_evidence', '').strip() for x in tests),
      [x['test_id'] for x in tests if not x.get('verification_method', '').strip() or not x.get('required_evidence', '').strip()])
p0_trace = [x for x in trace if x['row_kind'] in
            ('COMMUNICATION_REQUIREMENT', 'COMMUNICATION_OBSERVATION', 'RUBRIC_SUBSCALE')]
check('p0_agent_host_trainer_mapping_proposals_present', len(p0_trace) == 39 and all(
      all(x.get(k, '').strip() for k in ['agent_contract_refs', 'host_enforcement', 'trainer_tags',
                                      'agent_host_trainer_mapping_status']) for x in p0_trace),
      {'required_rows': 39, 'actual_rows': len(p0_trace)})

atlas = load(OLD / 'sources/atlas_data.json')
node_ids = {f"graph:{v['diagram']}/{k}" for k, v in atlas['nodes'].items()}
bad_refs = []
for table, name in [(trace, 'trace'), (tests, 'tests')]:
    for row in table:
        for ref in re.findall(r'graph:\d{2}/[A-Z]\d{2}', row['graph_node_ids']):
            if ref not in node_ids:
                bad_refs.append({'table': name, 'ref': ref})
check('namespaced_graph_node_references_resolve', not bad_refs, bad_refs)
used_nodes = set(re.findall(r'graph:\d{2}/[A-Z]\d{2}', ';'.join(x['graph_node_ids'] for x in trace)))
warnings.append({'type': 'DRAFT_ATLAS_NODES_NOT_MAPPED_TO_REQUIREMENTS',
                 'mapped_count': len(used_nodes), 'total_count': len(node_ids),
                 'unmapped': sorted(node_ids - used_nodes),
                 'meaning': 'Conceptual trace coverage only; see source audit for engineering gate impact.'})

register = load(ROOT / 'RULE_PROVENANCE_V3.json')
rule_map = {r['rule_id']: r for r in register['rules']}
check('independent_weight_fixture_sums', sum(rule_map['score.technical_subweights']['value'].values()) == 60 and
      sum(rule_map['score.communication_subweights']['value'].values()) == 40,
      {'technical': rule_map['score.technical_subweights']['value'], 'communication': rule_map['score.communication_subweights']['value']})
bonus = rule_map['score.bonus']['value']
check('v3_bonus_disabled_no_inherited_cap', bonus['enabled'] is False and bonus['user_hypothesis_range'] == [10, 15]
      and bonus['formula'] is None and 'cap' not in bonus, bonus)
check('all_rules_have_origin_status_and_no_production_activation', all(r['source_ref'] and
      r['source_version'] == SHA and r['validation_state'] and r['configurable'] and
      r['approved_for_production'] is False and r['effective_from'] is None for r in register['rules']),
      {'rules': len(register['rules']), 'status': register['status']})

repo = '[LOCAL_PATH_REDACTED]'
status = subprocess.run(['git', '-C', repo, 'status', '--short'], text=True, capture_output=True)
head = subprocess.run(['git', '-C', repo, 'rev-parse', 'HEAD'], text=True, capture_output=True)
check('original_checkout_unchanged', status.returncode == 0 and not status.stdout.strip() and
      head.stdout.strip() == '6898e563b6cab76517dad13919f7d3c172881f7c',
      {'head': head.stdout.strip(), 'status': status.stdout.strip()})

required_docs = ['BASELINE_DELTA_RECEIPT.md', 'ARCHITECTURE_READINESS_V3.md', 'SOURCE_AUDIT_V3.md',
                 'MVP_IMPLEMENTATION_PLAN_V3.md', 'LOCAL_PROTOTYPE_DESIGN_V3.md', 'DECISIONS_REQUIRED_V3.md',
                 'REBASED_SOURCE_TRACEABILITY.csv', 'ACCEPTANCE_TEST_MATRIX_V3.csv', 'RULE_PROVENANCE_V3.json']
check('required_artifacts_present', all((ROOT / p).is_file() for p in required_docs),
      [p for p in required_docs if not (ROOT / p).is_file()])

report = {'scope': 'source and document consistency only; NOT TIA application acceptance',
          'source_commit': SHA, 'source_date': '2026-10-19 Asia/Shanghai',
          'prior_test_status': 'CARRIED_FORWARD_PASS: 287 HAL + 52 Witness mock; no rerun at v3 SHA',
          'checks': checks, 'known_source_warnings': warnings,
          'summary': dict(Counter(x['status'] for x in checks))}
(ROOT / 'receipts/rebase_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'summary': report['summary'], 'failed': [x for x in checks if x['status'] == 'FAIL'],
                  'known_source_warnings': warnings}, ensure_ascii=False, indent=2))
raise SystemExit(1 if any(x['status'] == 'FAIL' for x in checks) else 0)
