"""Provider-neutral model boundary. This slice has no live provider transport.

Model text is untrusted presentation content: it cannot carry a score, state
transition or executable command. The controller remains authoritative.
"""

import asyncio
from dataclasses import dataclass, field
import json
import math
from typing import Any, Dict, Iterable, Optional, Protocol


_ROLES = frozenset({"interviewer", "trainer"})
_ERROR_CODES = frozenset({
    "INVALID_CONFIG", "INVALID_REQUEST", "LIVE_PROVIDER_DISABLED",
    "UNKNOWN_OPERATION", "PROVIDER_TIMEOUT", "PROVIDER_ERROR",
    "INVALID_RESPONSE",
})


class ModelPortalError(Exception):
    """Stable public error; raw provider exception messages are never exposed."""

    def __init__(self, code: str):
        self.code = code if code in _ERROR_CODES else "PROVIDER_ERROR"
        super().__init__(self.code)


@dataclass(frozen=True)
class ModelConfig:
    provider: str = "offline_mock"
    timeout_seconds: float = 1.0
    max_response_chars: int = 2000

    def __post_init__(self) -> None:
        try:
            valid_timeout = (
                type(self.timeout_seconds) in (int, float) and
                math.isfinite(self.timeout_seconds) and self.timeout_seconds > 0
            )
        except OverflowError:
            valid_timeout = False
        if (type(self.provider) is not str or not self.provider or
                not valid_timeout or
                type(self.max_response_chars) is not int or
                self.max_response_chars <= 0):
            raise ModelPortalError("INVALID_CONFIG")


@dataclass(frozen=True)
class ModelRequest:
    role: str
    operation: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelResponse:
    role: str
    text: str
    provenance: str = "SIMULATED"


class ModelAdapter(Protocol):
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Return only role-tagged presentation text, never controller actions."""
        ...


_MOCK_TEXT = {
    "brief": (
        "interviewer",
        "SIMULATED interview: explain how you would find each customer's first "
        "order. Clarify ties and missing values before describing your plan. "
        "This demonstration does not execute SQL or calculate scores.",
    ),
    "clarify": (
        "interviewer",
        "For this fixture, return one order per customer. Break equal timestamps "
        "using the smallest order ID, and exclude missing timestamps.",
    ),
    "feedback": (
        "interviewer",
        "You have described a plan. State what you have established, the remaining "
        "uncertainty, and how you would test ties and missing timestamps. "
        "No SQL result or capability score has been verified.",
    ),
    "close": (
        "interviewer",
        "Please conclude with what you established and what remains unverified. "
        "The host will close the interview and record a review before granting "
        "the separate Trainer access to its frozen receipt.",
    ),
    "drill": (
        "trainer",
        "Communication practice: give a short progress report stating what you "
        "proved, the specific gap, what you already tried, and one bounded help "
        "request. Then explain the next action you would take after feedback. "
        "This is a synthetic drill, not a score or a verified learning result.",
    ),
}


class OfflineMockAdapter:
    """Deterministic fixture dialogue with explicit failure-injection controls."""

    def __init__(
        self,
        error_operations: Iterable[str] = (),
        timeout_operations: Iterable[str] = (),
    ) -> None:
        self.error_operations = frozenset(error_operations)
        self.timeout_operations = frozenset(timeout_operations)

    async def generate(self, request: ModelRequest) -> ModelResponse:
        if request.operation not in _MOCK_TEXT:
            raise ModelPortalError("UNKNOWN_OPERATION")
        role, text = _MOCK_TEXT[request.operation]
        if request.role != role:
            raise ModelPortalError("INVALID_REQUEST")
        if request.operation in self.error_operations:
            raise RuntimeError("Synthetic provider failure")
        if request.operation in self.timeout_operations:
            # A cancellable suspension exercises a real wait_for timeout without
            # busy looping, sleeping for minutes, or contacting any service.
            await asyncio.Event().wait()
        return ModelResponse(role=role, text=text)


class FutureOpenAIAdapter:
    """Explicit integration seam; no credentials, SDK, HTTP, or environment reads."""

    async def generate(self, request: ModelRequest) -> ModelResponse:
        raise ModelPortalError("LIVE_PROVIDER_DISABLED")


class ModelPortal:
    def __init__(self, config: ModelConfig, adapter: ModelAdapter) -> None:
        if type(config) is not ModelConfig:
            raise ModelPortalError("INVALID_CONFIG")
        if config.provider != "offline_mock" or isinstance(adapter, FutureOpenAIAdapter):
            raise ModelPortalError("LIVE_PROVIDER_DISABLED")
        self.config = config
        self.adapter = adapter

    async def request(self, request: ModelRequest) -> ModelResponse:
        if (type(request) is not ModelRequest or
                type(request.role) is not str or request.role not in _ROLES or
                type(request.operation) is not str or
                not request.operation or len(request.operation) > 64 or
                type(request.context) is not dict):
            raise ModelPortalError("INVALID_REQUEST")
        try:
            # Reject arbitrary objects and non-finite values at the transport seam.
            json.dumps(request.context, allow_nan=False)
        except (TypeError, ValueError, RecursionError):
            raise ModelPortalError("INVALID_REQUEST") from None
        try:
            result = await asyncio.wait_for(
                self.adapter.generate(request), timeout=self.config.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise ModelPortalError("PROVIDER_TIMEOUT") from None
        except ModelPortalError as exc:
            raise ModelPortalError(exc.code) from None
        except Exception:
            raise ModelPortalError("PROVIDER_ERROR") from None
        if (type(result) is not ModelResponse or
                set(vars(result)) != {"role", "text", "provenance"} or
                type(result.role) is not str or result.role != request.role or
                type(result.text) is not str or not result.text.strip() or
                len(result.text) > self.config.max_response_chars or
                type(result.provenance) is not str or
                result.provenance != "SIMULATED"):
            raise ModelPortalError("INVALID_RESPONSE")
        return result


def build_portal(
    config: Optional[ModelConfig] = None,
    adapter: Optional[ModelAdapter] = None,
) -> ModelPortal:
    """Construct an offline portal. Custom adapters are local test fixtures only."""
    selected_config = config if config is not None else ModelConfig()
    selected_adapter = adapter if adapter is not None else OfflineMockAdapter()
    return ModelPortal(selected_config, selected_adapter)
