#!/usr/bin/env python3
"""Explicit, no-overwrite migration of Witness Loop v1/v2 saves. No credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

NAMES = {'session-v2.json': 'hal-session/v2', 'session.json': 'hal-session/v1'}
LIMIT = 2_000_000

def read_save(path, schema):
    if path.is_symlink() or not hasattr(os, 'O_NOFOLLOW'):
        raise ValueError('Unsafe save or unsupported platform')
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
            raise ValueError('Invalid save type or size')
        with os.fdopen(os.dup(fd), 'rb') as stream:
            content = stream.read(LIMIT + 1)
    finally:
        os.close(fd)
    if len(content) > LIMIT:
        raise ValueError('Oversized save')
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError('Duplicate JSON key')
            obj[key] = value
        return obj
    def invalid_constant(_):
        raise ValueError('Invalid JSON number')
    value = json.loads(content.decode('utf-8'), object_pairs_hook=unique, parse_constant=invalid_constant)
    if not isinstance(value, dict) or value.get('schema') != schema or value.get('domain_id') != 'witness-loop':
        raise ValueError('Save schema mismatch')
    # Full state and receipt validation remains authoritative in HAL Core at load.
    return content

def migrate(source, target, apply=False):
    source, target = Path(source).expanduser(), Path(target).expanduser()
    if not source.is_dir() or source.is_symlink() or target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ValueError('Invalid source or destination directory')
    if any((target / name).exists() or (target / name).is_symlink() for name in NAMES):
        raise ValueError('Existing destination save: refusing to overwrite')
    payloads = [(name, read_save(source / name, schema)) for name, schema in NAMES.items() if (source / name).exists() or (source / name).is_symlink()]
    if not payloads:
        print('NO_SAVES_TO_MIGRATE')
        return
    for name, content in payloads:
        print(('COPY' if apply else 'DRY_RUN'), name, len(content), hashlib.sha256(content).hexdigest())
    if not apply:
        print('NO_CHANGES_MADE: rerun with --apply when app is closed')
        return
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    if target.is_symlink():
        raise ValueError('Unsafe destination directory')
    created = []
    try:
        for name, content in payloads:
            fd = os.open(str(target / name), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            created.append(target / name)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
    except OSError:
        for path in created:
            try: path.unlink()
            except OSError: pass
        raise
    print('MIGRATION_COPIED; originals unchanged; HAL validates on next app launch')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument('--source-dir', type=Path, default=root / 'integrations/witness_loop/data')
    parser.add_argument('--target-dir', type=Path, default=Path.home() / 'Library/Application Support/Witness Loop')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        migrate(args.source_dir, args.target_dir, args.apply)
    except (OSError, ValueError, UnicodeError) as error:
        print('MIGRATION_STOPPED:', error, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
