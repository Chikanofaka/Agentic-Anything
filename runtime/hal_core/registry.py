"""Reviewed host bindings. Package declarations never supply executable targets."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from trusted_adapters.research import run as research_run
from trusted_adapters.returns import run as returns_run


class Port(str, Enum):
    LOCAL_CALCULATE = 'LOCAL_CALCULATE'
    LOCAL_TRIAGE = 'LOCAL_TRIAGE'
    LLM_DIRECT = 'LLM_DIRECT'
    MANAGED_AGENT = 'MANAGED_AGENT'
    EMBEDDED_CHANNEL = 'EMBEDDED_CHANNEL'
    DATA_FEED = 'DATA_FEED'
    TOOL_API = 'TOOL_API'


@dataclass(frozen=True)
class ToolBinding:
    id: str
    port: Port
    input_contract: str
    output_contract: str
    permissions: tuple[str, ...]
    capabilities: frozenset[str]
    handler: Callable[[dict], dict]


TRUSTED = {
    ('research-diagnostics', 'calculate-margin'): ToolBinding(
        'calculate-margin', Port.LOCAL_CALCULATE,
        'research-margin-input/v1', 'research-margin-output/v1',
        (), frozenset({'calculate'}), research_run),
    ('returns-operations', 'triage-return'): ToolBinding(
        'triage-return', Port.LOCAL_TRIAGE,
        'returns-triage-input/v1', 'returns-triage-output/v1',
        (), frozenset({'triage'}), returns_run),
}


def binding_matches(declared: dict, binding: ToolBinding) -> bool:
    """Match the entire declared executable contract to the trusted host record."""
    return (
        declared['id'] == binding.id
        and declared['port'] == binding.port.value
        and declared['input_contract'] == binding.input_contract
        and declared['output_contract'] == binding.output_contract
        and tuple(declared['permissions']) == binding.permissions
    )
