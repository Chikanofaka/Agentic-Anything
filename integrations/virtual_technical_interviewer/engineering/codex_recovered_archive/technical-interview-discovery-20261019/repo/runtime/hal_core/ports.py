"""Resolve declared capabilities against host evidence, never imagined live access."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import Port, TRUSTED, binding_matches

if TYPE_CHECKING:
    from .contracts import Inspection

LOCAL_PORTS = {Port.LOCAL_CALCULATE.value, Port.LOCAL_TRIAGE.value}
DIRECT_MODELS = {'openai', 'anthropic', 'deepseek', 'qwen'}
MANAGED_AGENTS = {'manus', 'workbuddy'}


def feature_status(pkg: Inspection, feature_id: str, provider: str | None = None):
    contract = pkg.contract
    feature = next((f for f in contract['features'] if f['id'] == feature_id), None)
    if feature is None:
        return {'status': 'BLOCKED', 'reason': 'UNKNOWN_FEATURE',
                'missing_ports': [], 'missing_permissions': [], 'checks': [],
                'provider': provider, 'live_model_verified': False}

    tool = next(t for t in contract['tools'] if t['id'] == feature['tool'])
    binding = TRUSTED.get((contract['id'], tool['id']))
    missing = []
    checks = []
    # Requests are declarations, not grants. This offline host has no effect grants.
    missing_permissions = sorted(set(feature['permissions']) | set(tool['permissions']))
    matched = binding is not None and binding_matches(tool, binding)
    if binding is None:
        missing.append(tool['port'] + ':NO_CURATED_BINDING')
    elif not matched:
        missing.append(tool['port'] + ':TOOL_CONTRACT_MISMATCH')

    requirements = feature['required_capabilities']
    if tool['port'] not in {r['port'] for r in requirements}:
        missing.append(tool['port'] + ':TOOL_PORT_NOT_REQUIRED')

    for requirement in requirements:
        port = requirement['port']
        capabilities = requirement['capabilities']
        if port in LOCAL_PORTS or (port == Port.TOOL_API.value and binding is not None):
            if not matched or binding.port.value != port:
                reason = port + ':NO_CURATED_BINDING'
                if reason not in missing:
                    missing.append(reason)
                continue
            absent = sorted(set(capabilities) - binding.capabilities)
            if absent:
                missing.extend(port + ':MISSING_CAPABILITY:' + c for c in absent)
            else:
                checks.append({'port': port, 'state': 'AVAILABLE_CURATED_LOCAL',
                               'tool': binding.id, 'capabilities': sorted(binding.capabilities)})
        elif port == Port.LLM_DIRECT.value:
            if not provider:
                missing.append(port + ':NO_PROVIDER')
            elif provider in MANAGED_AGENTS:
                missing.append('MANAGED_AGENT_PORT_MISMATCH')
            elif provider in DIRECT_MODELS:
                missing.append(port + ':UNVERIFIED_LIVE_CREDENTIALS_AND_CAPABILITIES')
            else:
                missing.append(port + ':UNSUPPORTED_PROVIDER')
        else:
            missing.append(port + ':NO_REGISTERED_ADAPTER')

    return {
        'status': 'BLOCKED' if missing or missing_permissions else 'AVAILABLE_CURATED_LOCAL',
        'tool': tool['id'], 'tool_contract_verified': matched,
        'declared_capabilities': requirements,
        'missing_ports': missing, 'missing_permissions': missing_permissions,
        'checks': checks, 'provider': provider, 'live_model_verified': False,
    }
