"""Bounded data-only inspection. No extraction, imported code execution or trust grant."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import unicodedata
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path

from .schema import ContractError, LEGACY_SCHEMA, normalize

MAX_FILES = 1500
MAX_PACKAGE_BYTES = 25_000_000
MAX_FILE_BYTES = 4_000_000
MAX_ARCHIVE_BYTES = 30_000_000
MAX_COMPRESSION_RATIO = 200
DENIED_BASENAMES = {'.env', 'id_rsa', 'id_ed25519', 'credentials.json', 'secrets.json', '.npmrc', '.pypirc'}
DENIED_SEGMENTS = {'.git', '__pycache__', '.ssh', 'node_modules'}
RESERVED = re.compile(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)', re.I)


@dataclass(frozen=True)
class Inspection:
    manifest: dict
    digest: str
    files: tuple[str, ...]
    warnings: tuple[str, ...]
    package_kind: str
    contract: dict
    archive_root: str | None = None

    def public(self):
        return {'package_id': self.manifest['id'], 'schema_version': self.manifest['schema_version'],
                'normalized_schema_version': self.contract['schema_version'], 'contract': self.contract,
                'digest': self.digest, 'files': list(self.files), 'warnings': list(self.warnings),
                'execution_policy': 'CURATED_ADAPTERS_ONLY', 'package_kind': self.package_kind,
                'archive_root': self.archive_root, 'publisher_verified': False}


def _safe_path(name):
    if not isinstance(name, str) or not name or len(name) > 1024 or '\\' in name or ':' in name:
        raise ContractError('INVALID_PACKAGE_PATH')
    try:
        encoded = name.encode('utf-8')
    except UnicodeError:
        raise ContractError('INVALID_PACKAGE_PATH') from None
    if len(encoded) > 1024 or any(ord(c) < 32 or ord(c) == 127 for c in name) or unicodedata.normalize('NFC', name) != name:
        raise ContractError('INVALID_PACKAGE_PATH')
    parts = name.split('/')
    if len(parts) > 32:
        raise ContractError('PACKAGE_TOO_DEEP')
    if any(p in ('', '.', '..') for p in parts):
        raise ContractError('PATH_TRAVERSAL')
    if any(p.endswith((' ', '.')) or RESERVED.match(p) for p in parts):
        raise ContractError('NONPORTABLE_PACKAGE_PATH')
    if any(p.casefold() in DENIED_SEGMENTS for p in parts):
        raise ContractError('RESTRICTED_SOURCE_PATH')
    if any(p.casefold() in DENIED_BASENAMES or p.casefold().startswith('.env.') or
           p.casefold().endswith(('.pem', '.key', '.p12')) for p in parts):
        raise ContractError('POTENTIAL_SECRET_FILE')
    return name


class _Inventory:
    def __init__(self):
        self.paths = {}
        self.spellings = {}
        self.total = 0

    def add(self, name, is_dir, size):
        _safe_path(name)
        if len(self.paths) >= MAX_FILES:
            raise ContractError('TOO_MANY_FILES')
        if name.casefold() in self.paths:
            raise ContractError('DUPLICATE_PATH')
        parts = name.split('/')
        for index in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:index])
            folded = prefix.casefold()
            if folded in self.spellings and self.spellings[folded] != prefix:
                raise ContractError('CASE_COLLISION')
            self.spellings[folded] = prefix
            if index < len(parts) and self.paths.get(folded) is False:
                raise ContractError('FILE_DIRECTORY_COLLISION')
        if not is_dir and any(p.startswith(name.casefold() + '/') for p in self.paths):
            raise ContractError('FILE_DIRECTORY_COLLISION')
        self.paths[name.casefold()] = is_dir
        if size < 0 or size > MAX_FILE_BYTES:
            raise ContractError('FILE_TOO_LARGE')
        self.total += size
        if self.total > MAX_PACKAGE_BYTES:
            raise ContractError('PACKAGE_TOO_LARGE')


def _read_directory(root):
    inventory = _Inventory()
    names = {}
    # Descriptor-relative traversal avoids following a swapped child/ancestor symlink.
    # Unsupported platforms must use ZIP inspection until a native reader exists.
    if not hasattr(os, 'O_NOFOLLOW') or os.open not in os.supports_dir_fd or os.scandir not in os.supports_fd:
        raise ContractError('SAFE_DIRECTORY_IMPORT_UNSUPPORTED')
    flags = os.O_RDONLY | os.O_NOFOLLOW

    def walk(fd, prefix='', depth=0):
        if depth > 32:
            raise ContractError('PACKAGE_TOO_DEEP')
        with os.scandir(fd) as entries:
            for entry in entries:
                name = prefix + entry.name
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    raise ContractError('SYMLINK_NOT_ALLOWED')
                is_dir = stat.S_ISDIR(info.st_mode)
                if not is_dir and not stat.S_ISREG(info.st_mode):
                    raise ContractError('SPECIAL_FILE_NOT_ALLOWED')
                inventory.add(name, is_dir, 0 if is_dir else info.st_size)
                child = os.open(entry.name, flags | (os.O_DIRECTORY if is_dir else os.O_NONBLOCK), dir_fd=fd)
                try:
                    actual = os.fstat(child)
                    if (actual.st_dev, actual.st_ino, actual.st_mode, actual.st_size) != (info.st_dev, info.st_ino, info.st_mode, info.st_size):
                        raise ContractError('PACKAGE_CHANGED_DURING_READ')
                    if is_dir:
                        walk(child, name + '/', depth + 1)
                    else:
                        with os.fdopen(os.dup(child), 'rb') as stream:
                            data = stream.read(MAX_FILE_BYTES + 1)
                        after = os.fstat(child)
                        if len(data) != info.st_size or after.st_mtime_ns != actual.st_mtime_ns or after.st_size != actual.st_size:
                            raise ContractError('PACKAGE_CHANGED_DURING_READ')
                        names[name] = data
                finally:
                    os.close(child)
    fd = os.open(root, flags | os.O_DIRECTORY)
    try:
        walk(fd)
    finally:
        os.close(fd)
    return names


def _read_zip(root, expected):
    if not hasattr(os, 'O_NOFOLLOW'):
        raise ContractError('SAFE_ZIP_IMPORT_UNSUPPORTED')
    fd = os.open(root, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        actual = os.fstat(stream.fileno())
        if not stat.S_ISREG(actual.st_mode):
            raise ContractError('SPECIAL_FILE_NOT_ALLOWED')
        if (actual.st_dev, actual.st_ino, actual.st_size, actual.st_mtime_ns) != (expected.st_dev, expected.st_ino, expected.st_size, expected.st_mtime_ns):
            raise ContractError('PACKAGE_CHANGED_DURING_READ')
        if actual.st_size > MAX_ARCHIVE_BYTES:
            raise ContractError('ARCHIVE_TOO_LARGE')
        result = _read_zip_stream(stream)
        after = os.fstat(stream.fileno())
        if (actual.st_size, actual.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ContractError('PACKAGE_CHANGED_DURING_READ')
        return result


def _read_zip_stream(stream):
    inventory = _Inventory()
    members = []
    names = {}
    with zipfile.ZipFile(stream) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_FILES:
            raise ContractError('TOO_MANY_FILES')
        for info in infos:
            # orig_filename retains NUL characters that ZipInfo.filename truncates.
            raw = info.orig_filename
            is_dir = raw.endswith('/')
            name = raw[:-1] if is_dir else raw
            mode = stat.S_IFMT(info.external_attr >> 16)
            if mode == stat.S_IFLNK:
                raise ContractError('SYMLINK_NOT_ALLOWED')
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR) or (mode == stat.S_IFDIR and not is_dir) or (mode == stat.S_IFREG and is_dir):
                raise ContractError('SPECIAL_FILE_NOT_ALLOWED')
            inventory.add(name, is_dir, info.file_size)
            if is_dir and info.file_size:
                raise ContractError('INVALID_DIRECTORY_ENTRY')
            if info.flag_bits & 1:
                raise ContractError('ENCRYPTED_ZIP_NOT_ALLOWED')
            if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ContractError('UNSUPPORTED_ZIP_COMPRESSION')
            if info.file_size > max(1, info.compress_size) * MAX_COMPRESSION_RATIO:
                raise ContractError('EXCESSIVE_COMPRESSION_RATIO')
            if not is_dir:
                members.append((name, info))
        # Validate every member's metadata before reading any compressed contents.
        for name, info in members:
            with archive.open(info) as stream:
                data = stream.read(MAX_FILE_BYTES + 1)
            if len(data) != info.file_size or len(data) > MAX_FILE_BYTES:
                raise ContractError('ZIP_SIZE_MISMATCH')
            names[name] = data
    roots = [name for name in names if name.split('/')[-1] == 'harness.json']
    if not roots:
        raise ContractError('MISSING_MANIFEST')
    if len(roots) != 1:
        raise ContractError('AMBIGUOUS_PACKAGE_ROOT')
    if roots[0] == 'harness.json':
        return names, None
    if len(roots[0].split('/')) != 2:
        raise ContractError('UNSUPPORTED_PACKAGE_LAYOUT')
    wrapper = roots[0].split('/')[0]
    if any(name != wrapper.casefold() and not name.startswith(wrapper.casefold() + '/') for name in inventory.paths):
        raise ContractError('AMBIGUOUS_PACKAGE_ROOT')
    return {name[len(wrapper) + 1:]: data for name, data in names.items()}, wrapper


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def _constant(_value):
    raise ContractError('NON_FINITE_JSON')


def _float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ContractError('NON_FINITE_JSON')
    return number


def _integer(value):
    if len(value.lstrip('-')) > 1024:
        raise ContractError('JSON_NUMBER_TOO_LARGE')
    return int(value)


def parse_json(data):
    """Strict JSON for manifests and CLI payloads, with value-free diagnostics."""
    try:
        if len(data) > MAX_FILE_BYTES:
            raise ContractError('JSON_TOO_LARGE')
        return json.loads(data, object_pairs_hook=_pairs, parse_constant=_constant,
                          parse_float=_float, parse_int=_integer)
    except ContractError:
        raise
    except (UnicodeError, ValueError, RecursionError):
        raise ContractError('INVALID_JSON') from None


def inspect(path: str | Path) -> Inspection:
    try:
        root = Path(path)
        if root.is_symlink():
            raise ContractError('SYMLINK_NOT_ALLOWED')
        if not root.exists():
            raise ContractError('PACKAGE_NOT_FOUND')
        original = root.lstat()
        mode = original.st_mode
        if stat.S_ISDIR(mode):
            names = _read_directory(root)
            kind, wrapper = 'directory', None
        elif stat.S_ISREG(mode):
            names, wrapper = _read_zip(root, original)
            kind = 'zip'
        else:
            raise ContractError('SPECIAL_FILE_NOT_ALLOWED')
        if 'harness.json' not in names:
            raise ContractError('MISSING_MANIFEST')
        if sum(name.split('/')[-1] == 'harness.json' for name in names) != 1:
            raise ContractError('AMBIGUOUS_PACKAGE_ROOT')
        manifest = parse_json(names['harness.json'])
        contract = normalize(manifest, set(names), _safe_path)
        digest = hashlib.sha256()
        for name in sorted(names):
            digest.update(name.encode('utf-8') + b'\0' + hashlib.sha256(names[name]).digest())
        warnings = ['UNSIGNED_PACKAGE', 'LICENSE_NOT_VERIFIED', 'UNTRUSTED_SOURCE_NOT_EXECUTED']
        if manifest['schema_version'] == LEGACY_SCHEMA:
            warnings.append('LEGACY_SCHEMA_NORMALIZED')
        if wrapper:
            warnings.append('GITHUB_WRAPPER_NORMALIZED')
        return Inspection(manifest, digest.hexdigest(), tuple(sorted(names)), tuple(warnings), kind, contract, wrapper)
    except ContractError:
        raise
    except (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError):
        raise ContractError('INVALID_ZIP') from None
    except UnicodeError:
        raise ContractError('INVALID_PACKAGE_ENCODING') from None
    except OSError:
        raise ContractError('PACKAGE_READ_FAILED') from None
