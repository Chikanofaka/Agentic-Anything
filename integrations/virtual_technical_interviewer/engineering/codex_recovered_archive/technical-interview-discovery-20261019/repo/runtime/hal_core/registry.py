"""Reviewed host bindings. Package declarations never supply executable targets."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from trusted_adapters.research import run as research_run
from trusted_adapters.returns import run as returns_run
from trusted_adapters import witness


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
    ('witness-loop', 'witness-step'): ToolBinding(
        'witness-step', Port.TOOL_API,
        'witness-turn-input/v1', 'witness-turn-output/v1',
        (), frozenset({'narrative_state'}), witness.run),
}


@dataclass(frozen=True)
class InteractiveBinding:
    """Reviewed domain lifecycle; the shared host owns transactions and storage."""
    package_directory: str
    start: Callable
    validate_state: Callable
    classify_context: Callable
    prepare_turn: Callable
    finalize_turn: Callable
    act: Callable
    user_markdown: Callable
    migrate_v1: Callable
    context_metadata: Callable
    preview_turn: Callable
    public_view: Callable


INTERACTIVE = {
    'witness-loop': InteractiveBinding('witness', witness.start, witness.validate_state,
        witness.classify_context, witness.prepare_turn, witness.finalize_turn,
        witness.act, witness.user_markdown, witness.migrate_v1,
        witness.context_metadata, witness.preview_turn, witness.public_view),
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
