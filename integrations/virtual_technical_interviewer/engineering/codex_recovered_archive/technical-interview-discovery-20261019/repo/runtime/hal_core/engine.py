"""Bounded offline dispatch through reviewed callable and value contracts."""
from __future__ import annotations

import time
import uuid

from .contracts import inspect, ContractError
from .ports import feature_status
from .registry import TRUSTED, binding_matches
from trusted_adapters.value_contracts import validate_value, ValueContractError

DENIED_INPUT_KEYS = {'api_key', 'apikey', 'key', 'token', 'password', 'secret',
                     'credential', 'authorization'}


def run(package_path, feature, payload, *, max_tool_calls=1):
    started = time.monotonic()
    receipt = {'run_id': str(uuid.uuid4()), 'kind': 'DETERMINISTIC_OFFLINE',
               'feature': feature, 'status': 'BLOCKED', 'events': [],
               'live_model_used': False, 'external_writes': False}

    def event(code):
        receipt['events'].append({'code': code})

    try:
        package = inspect(package_path)
        contract = package.contract
        receipt.update(domain_id=contract['id'], package_digest=package.digest,
                       contract_schema=contract['schema_version'])
        event('PACKAGE_INSPECTED')
        if type(max_tool_calls) is not int or max_tool_calls != 1:
            raise ContractError('TOOL_BUDGET_INVALID')
        if not isinstance(payload, dict) or any(str(k).lower() in DENIED_INPUT_KEYS for k in payload):
            raise ContractError('SECRET_LIKE_OR_INVALID_PAYLOAD')

        status = feature_status(package, feature)
        if status['status'] != 'AVAILABLE_CURATED_LOCAL':
            receipt['missing_ports'] = status['missing_ports']
            receipt['missing_permissions'] = status['missing_permissions']
            raise ContractError(status.get('reason', 'FEATURE_PORT_NOT_AVAILABLE'))
        declared = next(t for t in contract['tools'] if t['id'] == status['tool'])
        binding = TRUSTED.get((contract['id'], declared['id']))
        if binding is None or not binding_matches(declared, binding):
            raise ContractError('NOT_IN_TRUSTED_REGISTRY')
        receipt.update(tool_id=binding.id, input_contract=binding.input_contract,
                       output_contract=binding.output_contract, permissions=[])
        event('FEATURE_RESOLVED')
        validate_value(binding.input_contract, payload)
        event('INPUT_VALIDATED')
        # The callable belongs to reviewed host source, never to the imported package.
        try:
            result = binding.handler(payload)
        except Exception:
            # A failed reviewed adapter is an error receipt, never a fake result.
            raise ContractError('TRUSTED_TOOL_EXECUTION_FAILED') from None
        event('TRUSTED_TOOL_EXECUTED')
        validate_value(binding.output_contract, result)
        event('OUTPUT_VALIDATED')
        receipt['result'] = result
        receipt['status'] = 'SUCCESS'
    except (ContractError, ValueContractError) as error:
        receipt['reason'] = str(error)
        event('EXECUTION_BLOCKED')
    except (ValueError, KeyError, TypeError, ArithmeticError):
        # Adapter exceptions must not echo input values, paths, or potential secrets.
        receipt['reason'] = 'TRUSTED_TOOL_CONTRACT_ERROR'
        event('EXECUTION_BLOCKED')
    receipt['elapsed_ms'] = round((time.monotonic() - started) * 1000, 2)
    return receipt
