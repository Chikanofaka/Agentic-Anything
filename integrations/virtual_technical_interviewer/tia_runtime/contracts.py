"""Data-only role contracts. The controller, not these prompts, grants authority."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath


class ContractError(ValueError):
    """A role contract is absent, malformed or exceeds the offline authority."""


@dataclass(frozen=True)
class RoleContract:
    role_id: str
    display_name: str
    active_states: tuple[str, ...]
    allowed_inputs: tuple[str, ...]
    forbidden_authorities: tuple[str, ...]
    documents: tuple[tuple[str, str], ...]
    version: str


_LIMITS = {
    "interviewer": (("INTERVIEWING",), ("public_task", "public_session_context", "candidate_events")),
    "trainer": (("TRAINING",), ("closed_reviewed_receipt",)),
}
_FORBIDDEN = (
    "state_mutation", "scoring", "test_execution", "answer_vault",
    "role_handoff", "provider_selection", "credentials",
)
_DOCUMENTS = {"identity": "identity.md", "soul": "soul.md", "instructions": "AGENTS.md"}


def _checked_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or "\\" in relative:
        raise ContractError("Contract document path must be a relative POSIX path")
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError("Contract document path escapes integration directory")
    try:
        resolved = root.joinpath(*path.parts).resolve(strict=True)
        resolved.relative_to(root)
        if not resolved.is_file() or not resolved.read_text(encoding="utf-8").strip():
            raise ContractError("Contract document must be a nonempty text file")
    except (OSError, UnicodeError, ValueError) as exc:
        raise ContractError("Contract document is missing, unsafe or unreadable") from exc
    return resolved


def load_roles(base_dir: str | Path) -> dict[str, RoleContract]:
    """Load the two reviewed roles without importing or executing package code.

    ``base_dir`` is the virtual_technical_interviewer directory. Manifest fields
    cannot expand permissions. Document text remains untrusted dialogue guidance.
    """
    root = Path(base_dir).resolve()
    try:
        manifest = json.loads(_checked_path(root, "agents/roles.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeError) as exc:
        raise ContractError("Invalid role manifest") from exc
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "mode", "source", "roles"}:
        raise ContractError("Unknown or missing role-manifest fields")
    if manifest["schema_version"] != "tia-roles/v1" or manifest["mode"] != "OFFLINE_SIMULATION":
        raise ContractError("Unsupported role contract version or mode")
    if not isinstance(manifest["source"], str) or not manifest["source"].strip():
        raise ContractError("Role contract source is required")
    entries = manifest["roles"]
    if not isinstance(entries, list) or len(entries) != 2:
        raise ContractError("Exactly Interviewer and Trainer roles are required")
    result = {}
    for entry in entries:
        required = {"role_id", "display_name", "active_states", "allowed_inputs", "forbidden_authorities", "documents"}
        if not isinstance(entry, dict) or set(entry) != required:
            raise ContractError("Unknown or missing role fields")
        role = entry["role_id"]
        if not isinstance(role, str) or role not in _LIMITS or role in result:
            raise ContractError("Unknown or duplicate role")
        states, inputs = _LIMITS[role]
        if entry["active_states"] != list(states) or entry["allowed_inputs"] != list(inputs):
            raise ContractError("Role cannot expand session or data access")
        if entry["forbidden_authorities"] != list(_FORBIDDEN):
            raise ContractError("Role cannot change host-only authorities")
        if not isinstance(entry["display_name"], str) or not entry["display_name"].strip():
            raise ContractError("Role display name is required")
        documents = entry["documents"]
        expected = {kind: f"agents/{role}/{filename}" for kind, filename in _DOCUMENTS.items()}
        if documents != expected:
            raise ContractError("Only the role's declared identity, soul and instructions are permitted")
        for relative in documents.values():
            _checked_path(root, relative)
        result[role] = RoleContract(
            role, entry["display_name"], states, inputs, _FORBIDDEN,
            tuple(documents.items()), manifest["schema_version"],
        )
    return result
