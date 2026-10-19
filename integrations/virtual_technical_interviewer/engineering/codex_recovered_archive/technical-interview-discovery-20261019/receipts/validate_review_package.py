from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
checks = []

def check(name, condition, detail):
    checks.append({'check': name, 'status': 'PASS' if condition else 'FAIL', 'detail': detail})

manifest = json.loads((ROOT / 'receipts/canonical_manifest.json').read_text())
mismatches = []
for item in manifest['files']:
    path = ROOT / 'repo' / item['path']
    if not path.is_file():
        mismatches.append(item['path']); continue
    data = path.read_bytes()
    digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if digest != item['sha']: mismatches.append(item['path'])
check('pinned_repository_blobs_unchanged_after_checks', not mismatches,
      {'count': len(manifest['files']), 'mismatches': mismatches, 'commit': manifest['commit']})

source_root = ROOT / 'repo/integrations/virtual_technical_interviewer'
html = (source_root / 'index.html').read_text()
atlas = json.JSONDecoder().raw_decode(html.split('const DATA=', 1)[1])[0]
original = (source_root / '粘贴的 Markdown (1)(6).md').read_text().splitlines()
check('embedded_source_matches_full_original', atlas['source_lines'] == original,
      {'original_lines': len(original), 'nodes': len(atlas['nodes']), 'diagrams': len(atlas['diagrams'])})

physical_edges = {}
semantic_edges = []
for code, svg in re.findall(r'(<svg data-graph="(\d+)"[\s\S]*?</svg>)', html):
    # The first capture is SVG markup; second is its graph ID.
    markup, graph = code, svg
    tree = ET.fromstring(markup)
    for element in tree.iter():
        if element.attrib.get('class') != 'edge': continue
        title = next((e.text for e in element if e.tag.endswith('title')), '')
        labels = [e.text or '' for e in element.iter() if e.tag.endswith('text')]
        physical_edges[graph + '/' + element.attrib['id']] = title
        semantic_edges.append((graph, title, tuple(labels)))

def rows(filename):
    with (ROOT / filename).open(newline='') as handle:
        return list(csv.DictReader(handle))

mapping = rows('SOURCE_TO_GRAPH_TO_REQUIREMENT.csv')
matrix = rows('ACCEPTANCE_TEST_MATRIX.csv')
expected_fr = {'FR%02d' % n for n in range(1, 11)}
mapped_fr = {v for row in mapping for v in row['requirement_ids'].split(';')}
tested_fr = {v for row in matrix for v in row['fr_ids'].split(';')}
check('all_p0_functional_contracts_mapped', expected_fr <= mapped_fr, sorted(mapped_fr))
check('all_p0_functional_contracts_have_planned_tests', expected_fr <= tested_fr, sorted(tested_fr))
invalid_nodes = [(row.get('mapping_id', row.get('test_id')), n)
                 for row in mapping + matrix for n in row['graph_node_ids'].split(';')
                 if n and n not in atlas['nodes']]
check('all_node_references_resolve', not invalid_nodes, invalid_nodes)
invalid_edges = [(row['mapping_id'], ref) for row in mapping
                 for ref in row['graph_edge_refs'].split(';')
                 if ref.strip() and ref.strip() not in physical_edges]
check('all_physical_edge_references_resolve', not invalid_edges, invalid_edges)
check('acceptance_cases_unique_and_honestly_not_run',
      len({row['test_id'] for row in matrix}) == len(matrix) and all(row['status'] == 'NOT_RUN' for row in matrix),
      {'count': len(matrix), 'statuses': sorted({row['status'] for row in matrix})})
check('trace_rows_unique', len({row['mapping_id'] for row in mapping}) == len(mapping), {'count': len(mapping)})

register = (ROOT / 'repo/issue_register_v0_1.md').read_text()
known_issues = set(re.findall(r'F\d\d-\d\d\d', register))
linked = {i.strip() for row in mapping for i in row['linked_issue_ids'].split(';') if i.strip() != 'UNVERIFIED'}
check('linked_issue_ids_exist', linked <= known_issues, {'known': sorted(known_issues), 'linked': sorted(linked)})
rules = json.loads((ROOT / 'RULE_PROVENANCE.json').read_text())
check('proposed_rules_have_source_status_and_configurability',
      all(all(k in rule for k in ['rule_id','authority','source_ref','validation_state','configurable']) for rule in rules['rules']),
      {'count':len(rules['rules']), 'not_runtime_configuration':rules['status']})
scores = next(rule['value'] for rule in rules['rules'] if rule['rule_id'] == 'score.base_caps')
check('current_plan1_caps_preserved', scores == {'technical':60,'communication':40}, scores)

original_status = subprocess.check_output(['git','-C','[LOCAL_PATH_REDACTED]','status','--porcelain'],text=True)
check('original_checkout_still_clean', original_status == '', original_status)

summary = {
 'scope':'artifact/source integrity; these checks are not interview application acceptance',
 'commit':manifest['commit'], 'checks':checks,
 'pass_count':sum(c['status']=='PASS' for c in checks),
 'fail_count':sum(c['status']=='FAIL' for c in checks),
 'known_gaps':{
  'missing_review_ids':sorted({'F03-001','F04-001','F05-001','F06-002'}-known_issues),
  'pdf':'9-page Atlas export, no review dialogue transcript; all 9 pages visually inspected',
  'rendered_edges':len(physical_edges),
  'unique_diagram_title_label_edges':len(set(semantic_edges)),
  'duplicate_renderings':len(physical_edges)-len(set(semantic_edges)),
  'interview_acceptance_not_run':len(matrix)
 }
}
(ROOT / 'receipts/review_package_validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
raise SystemExit(bool(summary['fail_count']))
