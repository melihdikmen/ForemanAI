"""Single entry point for all LLM calls (via OpenRouter), with token/cost logging.

Every call goes through `chat()` so the model name stays out of the code and
token usage / cost is logged in one place (see CLAUDE.md engineering rules).
"""

from __future__ import annotations

import logging
from typing import Any

from openai import NOT_GIVEN, OpenAI
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger("foremanai.llm")

_settings = get_settings()

# One shared client pointed at OpenRouter's OpenAI-compatible API.
# As a gateway it also owns resilience: retry transient failures (429/5xx) and cap latency.
_client = OpenAI(
    api_key=_settings.openrouter_api_key,
    base_url=_settings.openrouter_base_url,
    max_retries=3,  # automatic exponential-backoff retries on rate limits / 5xx
    timeout=30.0,  # seconds before a single call is abandoned
)


class LLMResult(BaseModel):
    """Result of one LLM call: the reply text plus token/cost accounting."""

    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None = None


def _extract_cost(usage: object) -> float | None:
    """Pull the dollar cost OpenRouter reports, whether it is a field or in model_extra."""
    if usage is None:
        return None
    direct = getattr(usage, "cost", None)
    if direct is not None:
        return direct
    extra = getattr(usage, "model_extra", None) or {}
    return extra.get("cost")


def chat(messages: list[dict[str, str]], *, temperature: float = 0.2) -> LLMResult:
    """Send chat messages to the configured model and return the reply with usage.

    messages: list of {"role": "system"|"user"|"assistant", "content": "..."}.
    The model name comes from settings (LLM_MODEL) and is never hard-coded.
    """
    response = _client.chat.completions.create(
        model=_settings.llm_model,
        messages=messages,
        temperature=temperature,
        extra_body={"usage": {"include": True}},  # ask OpenRouter to also report cost
    )
    usage = response.usage
    result = LLMResult(
        content=response.choices[0].message.content or "",
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        total_tokens=usage.total_tokens if usage else 0,
        cost_usd=_extract_cost(usage),
    )
    _log_usage(result.prompt_tokens, result.completion_tokens, result.total_tokens, result.cost_usd)
    return result


def _log_usage(prompt: int, completion: int, total: int, cost: float | None) -> None:
    """Log token counts and cost for one LLM call."""
    logger.info(
        "llm call model=%s tokens=%d/%d/%d cost=%s",
        _settings.llm_model,
        prompt,
        completion,
        total,
        f"${cost:.6f}" if cost is not None else "n/a",
    )


def complete(
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.2,
) -> tuple[Any, int, float | None]:
    """Run one tool-enabled chat completion for the agent loop.

    Returns (response_message, total_tokens, cost_usd). The message may contain
    tool_calls, which the caller executes and feeds back as 'tool' messages.
    """
    response = _client.chat.completions.create(
        model=_settings.llm_model,
        messages=messages,
        temperature=temperature,
        tools=tools or NOT_GIVEN,
        extra_body={"usage": {"include": True}},
    )
    usage = response.usage
    cost = _extract_cost(usage)
    _log_usage(
        usage.prompt_tokens if usage else 0,
        usage.completion_tokens if usage else 0,
        usage.total_tokens if usage else 0,
        cost,
    )
    return response.choices[0].message, (usage.total_tokens if usage else 0), cost
