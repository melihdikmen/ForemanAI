"""Work-order drafting tool. Produces a DRAFT only — it never writes to the database.

Persisting happens only when a human submits the draft (POST /work-orders) and a
foreman approves it. Keeping this tool write-free is a deliberate safety boundary:
the assistant cannot change state.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models import Priority


class WorkOrderDraft(BaseModel):
    """A work-order proposal. Same shape as the POST /work-orders body, so the UI can
    submit a draft from the agent as-is (one schema, no drift between the two)."""

    machine_code: str = Field(examples=["PRES-3"])
    title: str = Field(max_length=200)
    description: str
    proposed_actions: str
    priority: Priority = Priority.MEDIUM


def draft_work_order(
    machine_code: str,
    title: str,
    description: str,
    proposed_actions: str,
    priority: str = "medium",
) -> dict[str, Any]:
    """Validate and return a work-order DRAFT for human review. Does not save anything.

    Invalid input (e.g. an unknown priority) raises a ValidationError, which the agent
    loop turns into an error message so the model can correct itself.
    """
    draft = WorkOrderDraft(
        machine_code=machine_code,
        title=title,
        description=description,
        proposed_actions=proposed_actions,
        priority=Priority(priority),
    )
    return {
        "status": "draft",
        **draft.model_dump(mode="json"),
        "note": "Bu bir taslaktır; teknisyen onaya göndermeli, ustabaşı onaylamalı.",
    }
