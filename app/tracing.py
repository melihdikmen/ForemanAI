"""Langfuse tracing, switched off cleanly when no keys are configured.

One /ask request = one trace. Inside it, spans for each tool call, retriever search,
and every LLM call (as a "generation", with model, tokens and cost). The point is
debugging: when an answer is wrong, open the trace and see exactly what the model saw.

Everything here degrades to a no-op without LANGFUSE_* keys, so tests and local runs
never need a Langfuse account.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from app.config import get_settings

logger = logging.getLogger("foremanai.tracing")

_settings = get_settings()

# Any decorated function type; the decorator returns the same type it was given.
F = TypeVar("F", bound=Callable[..., Any])

# The Langfuse client, or None when tracing is disabled (no keys in .env).
_client: Any = None

if _settings.langfuse_public_key and _settings.langfuse_secret_key:
    from langfuse import Langfuse

    _client = Langfuse(
        public_key=_settings.langfuse_public_key,
        secret_key=_settings.langfuse_secret_key,
        host=_settings.langfuse_host,
    )
    logger.info("langfuse tracing enabled (host=%s)", _settings.langfuse_host)
else:
    logger.info("langfuse tracing disabled (no keys)")


def tracing_enabled() -> bool:
    """True when a Langfuse client was created from the configured keys."""
    return _client is not None


def traced(name: str, as_type: str) -> Callable[[F], F]:
    """Decorator: record the function as a Langfuse observation of the given type.

    as_type is one of Langfuse's observation types: "agent", "tool", "retriever",
    "generation" (LLM call), "span". Without keys it returns the function unchanged.
    """
    if _client is None:
        return lambda func: func
    from langfuse import observe

    return observe(name=name, as_type=as_type)  # type: ignore[return-value]


def update_span(**fields: Any) -> None:
    """Attach name/input/output/metadata to the current span (no-op when disabled)."""
    if _client is not None:
        _client.update_current_span(**fields)


def update_generation(
    *,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost_usd: float | None,
    output: Any = None,
) -> None:
    """Record model + usage + cost on the current LLM-call observation."""
    if _client is None:
        return
    _client.update_current_generation(
        model=model,
        usage_details={
            "input": prompt_tokens,
            "output": completion_tokens,
            "total": total_tokens,
        },
        cost_details={"total": cost_usd} if cost_usd is not None else None,
        output=output,
    )


def current_trace_id() -> str | None:
    """Id of the trace being recorded, for linking an API response to Langfuse."""
    return _client.get_current_trace_id() if _client is not None else None


def flush_traces() -> None:
    """Send buffered traces now; call before a short-lived process exits (eval script)."""
    if _client is not None:
        _client.flush()
