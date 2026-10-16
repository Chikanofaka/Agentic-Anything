"""Dependency-free versioned package contract; declarations never grant authority."""
from __future__ import annotations

import re

SCHEMA_VERSION = 'hal-domain/v1'
LEGACY_SCHEMA = 'hal-demo/v0.2'
HOST_API = 'hal-core/v1'
SAFE_ID = re.compile(r'^[a-z][a-z0-9-]{2,63}$')
VERSION = re.compile(r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$')
CONTRACT_ID = re.compile(r'^[a-z][a-z0-9-]{2,63}/v[1-9][0-9]*$')
PORTS = {'LOCAL_CALCULATE', 'LOCAL_TRIAGE', 'LLM_DIRECT', 'MANAGED_AGENT',
         'EMBEDDED_CHANNEL', 'DATA_FEED', 'TOOL_API'}
CAPABILITIES = {'calculate', 'triage', 'tool_calling', 'structured_output', 'streaming', 'narrative_state'}
PERMISSIONS = {'selected_files_read', 'network', 'external_write'}
POLICY = {'filesystem': 'selected_paths_only', 'external_write': 'approval_required'}
LOCAL = {
    'LOCAL_CALCULATE': ('calculate-margin', 'research-margin-input/v1', 'research-margin-output/v1', 'calculate'),
    'LOCAL_TRIAGE': ('triage-return', 'returns-triage-input/v1', 'returns-triage-output/v1', 'triage'),
}
SECRET_KEYS = {'apikey', 'secret', 'token', 'password', 'credential', 'credentials', 'authorization', 'accesstoken'}


class ContractError(ValueError):
    """A static diagnostic safe to place in a receipt."""


def reject_secret_fields(value, depth=0):
    if depth > 32:
        raise ContractError('MANIFEST_TOO_DEEP')
    if isinstance(value, dict):
        for key, child in value.items():
            if re.sub(r'[-_\s]', '', key).lower() in SECRET_KEYS:
                raise ContractError('SECRET_FIELD_IN_MANIFEST')
            reject_secret_fields(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            reject_secret_fields(child, depth + 1)


def _object(value, required, optional=()):
    if not isinstance(value, dict):
        raise ContractError('EXPECTED_OBJECT')
    if set(value) - set(required) - set(optional):
        raise ContractError('UNKNOWN_MANIFEST_FIELD')
    if set(required) - set(value):
        raise ContractError('MISSING_MANIFEST_FIELD')


def _text(value, pattern=None):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ContractError('INVALID_MANIFEST_STRING')
    try:
        value.encode('utf-8')
    except UnicodeError:
        raise ContractError('INVALID_MANIFEST_STRING') from None
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ContractError('INVALID_MANIFEST_STRING')
    if pattern and not pattern.fullmatch(value):
        raise ContractError('INVALID_MANIFEST_IDENTIFIER')


def _list(value, *, maximum=100, nonempty=False):
    if not isinstance(value, list) or len(value) > maximum or (nonempty and not value):
        raise ContractError('INVALID_MANIFEST_LIST')


def _enum_list(value, allowed):
    _list(value, maximum=15)
    if any(not isinstance(x, str) or x not in allowed for x in value):
        raise ContractError('UNKNOWN_CAPABILITY_OR_PERMISSION')
    if len(value) != len(set(value)):
        raise ContractError('DUPLICATE_DECLARATION')


def _assets(m, files, safe_path, *, v1):
    for key in ('id', 'name', 'version', 'domain'):
        _text(m[key], SAFE_ID if key in ('id', 'domain') else VERSION if key == 'version' else None)
    if 'description' in m:
        _text(m['description'])
    for key in (('entrypoint', 'readme', 'agents') if v1 else ('entrypoint', 'readme')):
        path = m[key]
        if not isinstance(path, str) or safe_path(path) != path or path not in files:
            raise ContractError('MISSING_REQUIRED_FILE:' + key)
    _list(m['skills'], maximum=30, nonempty=True)
    for path in m['skills']:
        if not isinstance(path, str) or safe_path(path) != path or path not in files:
            raise ContractError('MISSING_SKILL_FILE')
    if len(set(m['skills'])) != len(m['skills']):
        raise ContractError('DUPLICATE_DECLARATION')
    if m['permissions'] != POLICY:
        raise ContractError('UNSAFE_PERMISSION_DECLARATION')


COMMON = {'schema_version', 'id', 'name', 'version', 'domain', 'entrypoint', 'readme', 'skills', 'features', 'permissions'}


def validate_v1(m, files, safe_path):
    _object(m, COMMON | {'agents', 'host', 'tools'}, {'description'})
    _assets(m, files, safe_path, v1=True)
    if m['host'] != {'api': HOST_API}:
        raise ContractError('UNSUPPORTED_HOST_API')
    _list(m['tools'], nonempty=True)
    tools = {}
    for tool in m['tools']:
        _object(tool, {'id', 'port', 'input_contract', 'output_contract', 'permissions'})
        _text(tool['id'], SAFE_ID)
        if tool['id'] in tools:
            raise ContractError('DUPLICATE_TOOL_ID')
        if not isinstance(tool['port'], str) or tool['port'] not in PORTS:
            raise ContractError('UNKNOWN_PORT')
        _text(tool['input_contract'], CONTRACT_ID)
        _text(tool['output_contract'], CONTRACT_ID)
        _enum_list(tool['permissions'], PERMISSIONS)
        tools[tool['id']] = tool
    _list(m['features'], nonempty=True)
    features = set()
    for feature in m['features']:
        _object(feature, {'id', 'tool', 'required_capabilities', 'permissions'})
        _text(feature['id'], SAFE_ID)
        if feature['id'] in features:
            raise ContractError('DUPLICATE_FEATURE_ID')
        features.add(feature['id'])
        if not isinstance(feature['tool'], str) or feature['tool'] not in tools:
            raise ContractError('UNDECLARED_TOOL')
        _enum_list(feature['permissions'], PERMISSIONS)
        _list(feature['required_capabilities'], maximum=15, nonempty=True)
        ports = set()
        for requirement in feature['required_capabilities']:
            _object(requirement, {'port', 'capabilities'})
            port = requirement['port']
            if not isinstance(port, str) or port not in PORTS:
                raise ContractError('UNKNOWN_PORT')
            if port in ports:
                raise ContractError('DUPLICATE_REQUIRED_PORT')
            ports.add(port)
            _enum_list(requirement['capabilities'], CAPABILITIES)
        if tools[feature['tool']]['port'] not in ports:
            raise ContractError('TOOL_PORT_NOT_REQUIRED')
    return m


def normalize(m, files, safe_path):
    if not isinstance(m, dict):
        raise ContractError('MANIFEST_NOT_OBJECT')
    reject_secret_fields(m)
    version = m.get('schema_version')
    if version == SCHEMA_VERSION:
        return validate_v1(m, files, safe_path)
    if version != LEGACY_SCHEMA:
        raise ContractError('UNSUPPORTED_SCHEMA')
    _object(m, COMMON, {'description', 'model_requirements'})
    _assets(m, files, safe_path, v1=False)
    model = m.get('model_requirements', {})
    _object(model, set(), {'tool_calling'})
    if 'tool_calling' in model and type(model['tool_calling']) is not bool:
        raise ContractError('INVALID_MODEL_REQUIREMENT')
    _list(m['features'], nonempty=True)
    tools = {}
    features = []
    for feature in m['features']:
        _object(feature, {'id', 'required_ports'})
        _text(feature['id'], SAFE_ID)
        _enum_list(feature['required_ports'], PORTS)
        local = [p for p in feature['required_ports'] if p in LOCAL]
        if len(local) != 1:
            raise ContractError('LEGACY_MIGRATION_UNSUPPORTED')
        port = local[0]
        tool_id, inputs, outputs, capability = LOCAL[port]
        tools[tool_id] = {'id': tool_id, 'port': port, 'input_contract': inputs,
                          'output_contract': outputs, 'permissions': []}
        features.append({'id': feature['id'], 'tool': tool_id, 'permissions': [],
                         'required_capabilities': [
                             {'port': p, 'capabilities': [capability] if p == port else
                              ['tool_calling'] if p == 'LLM_DIRECT' and model.get('tool_calling') else []}
                             for p in feature['required_ports']]})
    normalized = {k: v for k, v in m.items() if k not in ('model_requirements', 'features')}
    normalized.update(schema_version=SCHEMA_VERSION, agents='AGENTS.md', host={'api': HOST_API},
                      tools=list(tools.values()), features=features)
    return validate_v1(normalized, files, safe_path)
