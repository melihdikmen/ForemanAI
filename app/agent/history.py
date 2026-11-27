"""Short-term (conversation) memory: the previous turns the client sends with a question.

The server is stateless; the UI keeps the chat and sends it back with every /ask.
The model only "remembers" what we put in front of it, so each request replays the
last few turns. Two rules keep this cheap and safe:

- Trim server-side. The client may send anything; we keep only the most recent turns
  and cut long ones, so the token budget cannot be blown by the caller.
- Replay only questions and final answers, never tool calls or retrieved chunks.
  The model can search again if it needs a manual; carrying chunks forward would
  multiply the prompt size every turn.

History is untrusted input (see the system prompt): a client could fabricate an
assistant turn claiming an action was taken.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# How many previous messages to replay (3 question/answer pairs). Enough for
# "and for ROBOT-1?" style follow-ups; small enough to keep cost roughly flat.
MAX_HISTORY_MESSAGES = 6
# Longest single message we replay; longer ones are cut (answers can be long).
MAX_MESSAGE_CHARS = 2000


class ChatTurn(BaseModel):
    """One earlier message in the conversation, as the client stored it."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=20_000)


def trim_history(history: list[ChatTurn]) -> list[dict[str, Any]]:
    """Return the last MAX_HISTORY_MESSAGES turns as chat messages, each cut to size.

    Cutting keeps the start of a message: for an answer that is where the diagnosis
    and the machine/alarm names are; the tail is usually safety boilerplate.
    """
    recent = history[-MAX_HISTORY_MESSAGES:]
    messages: list[dict[str, Any]] = []
    for turn in recent:
        content = turn.content
        if len(content) > MAX_MESSAGE_CHARS:
            content = content[:MAX_MESSAGE_CHARS] + " …"
        messages.append({"role": turn.role, "content": content})
    return messages


def build_messages(
    system_prompt: str, question: str, history: list[ChatTurn] | None
) -> list[dict[str, Any]]:
    """Assemble the initial message list: system prompt, trimmed history, new question."""
    return [
        {"role": "system", "content": system_prompt},
        *trim_history(history or []),
        {"role": "user", "content": question},
    ]
