"""Strict local manifest inspection. Never evaluates imported package code."""
from __future__ import annotations
import hashlib, json, re, stat, zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

MAX_FILES = 1500
MAX_PACKAGE_BYTES = 25_000_000
MAX_FILE_BYTES = 4_000_000
SAFE_ID = re.compile(r'^[a-z][a-z0-9-]{2,63}$')
SAFE_PORT = re.compile(r'^[A-Z][A-Z0-9_]{1,50}$')
DENIED_BASENAMES = {'.env', '.env.local', 'id_rsa', 'id_ed25519', 'credentials.json', 'secrets.json', '.npmrc', '.pypirc'}
DENIED_SEGMENTS = {'.git', '__pycache__', '.ssh', 'node_modules'}

class ContractError(ValueError):
    pass

@dataclass(frozen=True)
class Inspection:
    manifest: dict
    digest: str
    files: tuple[str, ...]
    warnings: tuple[str, ...]
    package_kind: str

    def public(self):
        return {'package_id': self.manifest['id'], 'schema_version': self.manifest['schema_version'],
                'digest': self.digest, 'files': list(self.files), 'warnings': list(self.warnings),
                'execution_policy': 'CURATED_ADAPTERS_ONLY', 'package_kind': self.package_kind}


def _safe_path(name):
    if not name or '\\' in name or '\x00' in name or name.startswith('/') or re.match(r'^[a-zA-Z]:', name):
        raise ContractError('INVALID_PACKAGE_PATH')
    normalized = name.rstrip('/')
    p = PurePosixPath(normalized)
    if normalized in ('.', '') or any(x in ('.', '..') for x in p.parts):
        raise ContractError('PATH_TRAVERSAL')
    if any(x in DENIED_SEGMENTS for x in p.parts):
        raise ContractError('RESTRICTED_SOURCE_PATH')
    if p.name.lower() in DENIED_BASENAMES or p.name.lower().endswith(('.pem','.key','.p12')):
        raise ContractError('POTENTIAL_SECRET_FILE')
    return normalized


def _validate_manifest(m, files):
    if not isinstance(m, dict): raise ContractError('MANIFEST_NOT_OBJECT')
    if m.get('schema_version') != 'hal-demo/v0.2': raise ContractError('UNSUPPORTED_SCHEMA')
    if not isinstance(m.get('id'),str) or not SAFE_ID.fullmatch(m['id']): raise ContractError('BAD_PACKAGE_ID')
    for k in ('entrypoint','readme'):
        v=m.get(k)
        if not isinstance(v,str) or _safe_path(v)!=v or v not in files: raise ContractError('MISSING_REQUIRED_FILE:'+k)
    skills=m.get('skills')
    if not isinstance(skills,list) or not skills or len(skills)>30: raise ContractError('INVALID_SKILLS')
    for x in skills:
        if not isinstance(x,str) or _safe_path(x)!=x or x not in files: raise ContractError('MISSING_SKILL_FILE')
    f=m.get('features')
    if not isinstance(f,list) or not f or len(f)>100: raise ContractError('INVALID_FEATURES')
    ids=set()
    for x in f:
        if not isinstance(x,dict) or not isinstance(x.get('id'),str) or not SAFE_ID.fullmatch(x['id']):
            raise ContractError('INVALID_FEATURE_ID')
        if x['id'] in ids: raise ContractError('DUPLICATE_FEATURE_ID')
        ids.add(x['id'])
        ports=x.get('required_ports')
        if not isinstance(ports,list) or not ports or len(ports)>15 or any(not isinstance(t,str) or not SAFE_PORT.fullmatch(t) for t in ports):
            raise ContractError('INVALID_REQUIRED_PORTS')
    permissions=m.get('permissions')
    if not isinstance(permissions,dict) or permissions.get('external_write')!='approval_required' or permissions.get('filesystem')!='selected_paths_only':
        raise ContractError('UNSAFE_PERMISSION_DECLARATION')
    for name in m.keys():
        if name.lower() in {'api_key','secret','token','password','credential'}: raise ContractError('SECRET_FIELD_IN_MANIFEST')
    # v0.2 is not a signed standard: a valid manifest alone never grants execute permission.


def inspect(path: str|Path) -> Inspection:
    root=Path(path)
    if not root.exists(): raise ContractError('PACKAGE_NOT_FOUND')
    names={}; total=0
    if root.is_dir():
        kind='directory'
        base=root.resolve()
        files=[p for p in root.rglob('*') if p.is_file() or p.is_symlink()]
        if len(files)>MAX_FILES: raise ContractError('TOO_MANY_FILES')
        for p in files:
            if p.is_symlink(): raise ContractError('SYMLINK_NOT_ALLOWED')
            rel=p.relative_to(root).as_posix(); _safe_path(rel)
            if not p.resolve().is_relative_to(base): raise ContractError('PATH_ESCAPE')
            if p.stat().st_size>MAX_FILE_BYTES: raise ContractError('FILE_TOO_LARGE')
            total+=p.stat().st_size
            if total>MAX_PACKAGE_BYTES: raise ContractError('PACKAGE_TOO_LARGE')
            names[rel]=p.read_bytes()
    else:
        kind='zip'
        if not zipfile.is_zipfile(root): raise ContractError('NOT_A_ZIP')
        with zipfile.ZipFile(root) as z:
            files=z.infolist()
            if len(files)>MAX_FILES: raise ContractError('TOO_MANY_FILES')
            for f in files:
                name=_safe_path(f.filename)
                if f.is_dir(): continue
                if stat.S_ISLNK(f.external_attr>>16): raise ContractError('SYMLINK_NOT_ALLOWED')
                if f.file_size>MAX_FILE_BYTES: raise ContractError('FILE_TOO_LARGE')
                total+=f.file_size
                if total>MAX_PACKAGE_BYTES: raise ContractError('PACKAGE_TOO_LARGE')
                if name in names: raise ContractError('DUPLICATE_PATH')
                names[name]=z.read(f)
    if not names or 'harness.json' not in names: raise ContractError('MISSING_MANIFEST')
    try: manifest=json.loads(names['harness.json'].decode('utf-8'))
    except (ValueError,UnicodeError): raise ContractError('INVALID_MANIFEST_JSON')
    _validate_manifest(manifest,set(names))
    # Streaming checksum over names and bytes; does not sign or authenticate publisher.
    h=hashlib.sha256()
    for k in sorted(names):
        h.update(k.encode('utf-8')+b'\0'+hashlib.sha256(names[k]).digest())
    warnings=['UNSIGNED_PACKAGE','LICENSE_NOT_VERIFIED','UNTRUSTED_SOURCE_NOT_EXECUTED']
    return Inspection(manifest,h.hexdigest(),tuple(sorted(names)),tuple(warnings),kind)
