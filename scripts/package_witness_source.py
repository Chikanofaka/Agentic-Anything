"""Build a reviewable source ZIP from explicit source roots; no state or keys."""
from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'integrations/witness_loop/dist/HAL_Witness_Loop_Source.zip'
TREES = (
    'runtime/hal_core', 'runtime/trusted_adapters', 'runtime/fixtures',
    'runtime/tests', 'runtime/docs', 'baseline/prd',
    'integrations/witness_loop/source', 'integrations/witness_loop/native',
    'integrations/witness_loop/ui',
)
FILES = (
    'AGENTS.md', 'README_START_HERE.md', '.gitignore', 'runtime/README.md',
    'status/HUMAN_GATE.md', 'engineering/BASELINE_AUDIT.md',
    'engineering/SPRINT1_RECEIPT.md', 'engineering/HAL_WITNESS_TYPE_B_PRD.md',
    'engineering/WITNESS_INTEGRATION_RECEIPT.md',
    'integrations/witness_loop/README.md',
    'integrations/witness_loop/SOURCE_PROVENANCE.md',
    'scripts/verify_local.sh', 'scripts/verify_witness_local.sh',
    'scripts/build_witness_mac.sh', 'scripts/package_witness_source.py',
)
SUFFIXES = {'.py', '.md', '.json', '.html', '.css', '.js', '.swift', '.csv'}


def main():
    paths = {ROOT / name for name in FILES}
    for name in TREES:
        for path in (ROOT / name).rglob('*'):
            if path.suffix in SUFFIXES and '__pycache__' not in path.parts:
                paths.add(path)
    contents = []
    for path in sorted(paths):
        if path.is_symlink() or not path.is_file() or path.resolve() != path:
            raise SystemExit('Unexpected source type: ' + str(path.relative_to(ROOT)))
        contents.append(('HAL_Witness_Loop/' + str(path.relative_to(ROOT)), path.read_bytes()))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents:
            entry = zipfile.ZipInfo(name, date_time=(2026, 10, 16, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        assert archive.namelist() == [name for name, _ in contents]
        assert all(archive.read(name) == data for name, data in contents)
    print(f'Source archive: {OUTPUT}')
    print(f'{len(contents)} reviewed source files; SHA-256 {hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}')


if __name__ == '__main__':
    main()
