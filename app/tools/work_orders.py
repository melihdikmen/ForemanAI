"""Work-order drafting tool. Produces a DRAFT only — it never writes to the database.

Persisting happens only when a human submits the draft (POST /work-orders) and a
foreman approves it. Keeping this tool write-free is a deliberate safety boundary:
the assistant cannot change state.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.db import ReadOnlySessionLocal
from app.models import Machine, Priority, WorkOrder, WorkOrderStatus
from app.tools.faults import UNTRUSTED_DATA_NOTICE, _tag_untrusted


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


def list_recent_rejections(machine_code: str, limit: int = 5) -> dict[str, Any]:
    """Return the foreman's most recent rejection reasons for one machine.

    This is the project's "long-term memory": decisions a human already made, read
    straight from work_orders instead of being copied into a separate memory store.
    The agent should consult it before drafting a work order, so a draft does not
    repeat something the foreman turned down last week.

    Names are deliberately left out (who rejected / who requested): the model needs
    the decision, not the person. Reasons are free text typed by a foreman, so they
    are tagged as untrusted data like fault records.

    Args:
        machine_code: machine to look up, e.g. "PRES-2".
        limit: how many of the newest rejections to return (capped at 10).
    """
    capped_limit = max(1, min(limit, 10))  # bound the context handed to the model

    with ReadOnlySessionLocal() as session:
        rows = session.execute(
            select(WorkOrder)
            .join(Machine)
            .where(Machine.code == machine_code, WorkOrder.status == WorkOrderStatus.REJECTED)
            .order_by(WorkOrder.reviewed_at.desc())
            .limit(capped_limit)
        ).scalars()
        rejections = [
            {
                "title": order.title,
                "rejected_on": order.reviewed_at.date().isoformat() if order.reviewed_at else None,
                "reason": _tag_untrusted(order.rejection_reason or "", tag="rejection_reason"),
            }
            for order in rows
        ]

    return {
        "machine_code": machine_code,
        "count": len(rejections),
        "notice": UNTRUSTED_DATA_NOTICE if rejections else None,
        "rejections": rejections,
    }
