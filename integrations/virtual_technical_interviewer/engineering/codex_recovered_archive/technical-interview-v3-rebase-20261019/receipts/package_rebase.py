"""Package only explicit review artifacts, v3 text sources and non-private receipts."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parent.parent
validation = json.loads((root / 'receipts/rebase_validation.json').read_text())
if validation['summary'].get('FAIL', 0):
    raise SystemExit('Resolve document validation failures before packaging.')
files = list(root.glob('*.md')) + list(root.glob('*.csv')) + list(root.glob('*.json'))
files = [p for p in files if p.name != 'ARTIFACT_MANIFEST.json']
files += [p for p in (root / 'sources/TIA_FULL_PRD_v3').iterdir()
          if p.suffix in ('.md', '.csv', '.json')]
files += [p for p in (root / 'receipts').iterdir()
          if p.is_file() and p.suffix in ('.json', '.py')]
files += list((root / 'receipts/carried_forward').glob('*'))
files = sorted(set(files))
manifest = []
for path in files:
    if not path.is_file() or path.is_symlink():
        raise SystemExit(f'Unexpected nonregular artifact: {path}')
    data = path.read_bytes()
    manifest.append({'path': str(path.relative_to(root)), 'bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest()})
manifest_path = root / 'ARTIFACT_MANIFEST.json'
manifest_path.write_text(json.dumps({'scope': 'Local review package; no original private transcript, Atlas or old repo copy',
                                     'source_commit': validation['source_commit'], 'files': manifest},
                                    ensure_ascii=False, indent=2) + '\n')
files.append(manifest_path)
archive = root.parent / 'TIA_v3_rebase_20261019.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as target:
    for path in files:
        target.write(path, 'TIA_v3_rebase_20261019/' + str(path.relative_to(root)))
with zipfile.ZipFile(archive) as result:
    if result.testzip() is not None:
        raise SystemExit('Archive CRC check failed')
    for entry in manifest:
        content = result.read('TIA_v3_rebase_20261019/' + entry['path'])
        if hashlib.sha256(content).hexdigest() != entry['sha256']:
            raise SystemExit('Archive content mismatch: ' + entry['path'])
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(archive.parent / (archive.name + '.sha256')).write_text(digest + '  ' + archive.name + '\n')
print(json.dumps({'archive': str(archive), 'files': len(files), 'bytes': archive.stat().st_size,
                  'sha256': digest, 'verification': 'ZIP_CRC_AND_ALL_ENTRY_SHA256_PASS'}, indent=2))
