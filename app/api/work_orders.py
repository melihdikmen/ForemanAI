"""Work-order endpoints: the human-in-the-loop side of the assistant.

The agent only produces drafts. A human (technician) submits a draft, which is
stored as PENDING; a foreman later approves or rejects it. The agent itself has
no path to these endpoints, so it can never change database state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, Role, get_current_user, get_db, require_role
from app.models import Machine, Priority, WorkOrder, WorkOrderStatus

router = APIRouter(prefix="/work-orders", tags=["work-orders"])


class WorkOrderSubmit(BaseModel):
    """Request body: a draft (as produced by draft_work_order) sent for approval."""

    machine_code: str = Field(examples=["PRES-3"])
    title: str = Field(max_length=200)
    description: str
    proposed_actions: str
    priority: Priority = Priority.MEDIUM


class WorkOrderOut(BaseModel):
    """Response body: one work order as stored in the database."""

    id: int
    machine_code: str
    status: WorkOrderStatus
    priority: Priority
    title: str
    description: str
    proposed_actions: str
    created_by: str
    created_at: datetime
    reviewed_by: str | None
    reviewed_at: datetime | None
    rejection_reason: str | None


class RejectRequest(BaseModel):
    """Request body for a rejection: the foreman must say why."""

    reason: str = Field(min_length=3)


def to_out(work_order: WorkOrder) -> WorkOrderOut:
    """Convert an ORM row to the API schema (flattening machine -> machine_code)."""
    return WorkOrderOut(
        id=work_order.id,
        machine_code=work_order.machine.code,
        status=work_order.status,
        priority=work_order.priority,
        title=work_order.title,
        description=work_order.description,
        proposed_actions=work_order.proposed_actions,
        created_by=work_order.created_by,
        created_at=work_order.created_at,
        reviewed_by=work_order.reviewed_by,
        reviewed_at=work_order.reviewed_at,
        rejection_reason=work_order.rejection_reason,
    )


# Type aliases so endpoint signatures stay short.
DbSession = Annotated[Session, Depends(get_db)]
User = Annotated[CurrentUser, Depends(get_current_user)]
Foreman = Annotated[CurrentUser, Depends(require_role(Role.FOREMAN))]


def get_pending_for_review(db: Session, work_order_id: int) -> WorkOrder:
    """Load a work order with a row lock and ensure it is still PENDING.

    The lock (SELECT ... FOR UPDATE) makes two foremen deciding at the same moment
    run one after the other, so an order cannot be both approved and rejected.
    """
    work_order = db.scalar(select(WorkOrder).where(WorkOrder.id == work_order_id).with_for_update())
    if work_order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"work order {work_order_id} not found")
    if work_order.status != WorkOrderStatus.PENDING:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"work order {work_order_id} is '{work_order.status}', only 'pending' can be reviewed",
        )
    return work_order


@router.post("", status_code=status.HTTP_201_CREATED)
def submit_work_order(body: WorkOrderSubmit, db: DbSession, user: User) -> WorkOrderOut:
    """Store a draft as PENDING so it appears in the foreman's approval queue."""
    machine = db.scalar(select(Machine).where(Machine.code == body.machine_code))
    if machine is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown machine: {body.machine_code}")

    work_order = WorkOrder(
        machine=machine,
        created_at=datetime.now(),
        created_by=user.name,
        status=WorkOrderStatus.PENDING,
        title=body.title,
        description=body.description,
        proposed_actions=body.proposed_actions,
        priority=body.priority,
    )
    db.add(work_order)
    db.commit()
    return to_out(work_order)


@router.get("")
def list_work_orders(
    db: DbSession,
    user: User,  # unused in the body, but forces the caller to identify (401 otherwise)
    status_filter: Annotated[WorkOrderStatus | None, Query(alias="status")] = None,
) -> list[WorkOrderOut]:
    """List work orders, newest first; optionally filter by status (e.g. ?status=pending)."""
    query = select(WorkOrder).order_by(WorkOrder.created_at.desc())
    if status_filter is not None:
        query = query.where(WorkOrder.status == status_filter)
    return [to_out(work_order) for work_order in db.scalars(query)]


@router.post("/{work_order_id}/approve")
def approve_work_order(work_order_id: int, db: DbSession, foreman: Foreman) -> WorkOrderOut:
    """Foreman approves a PENDING work order. This is the only path to APPROVED."""
    work_order = get_pending_for_review(db, work_order_id)
    work_order.status = WorkOrderStatus.APPROVED
    work_order.reviewed_by = foreman.name
    work_order.reviewed_at = datetime.now()
    db.commit()
    return to_out(work_order)


@router.post("/{work_order_id}/reject")
def reject_work_order(
    work_order_id: int, body: RejectRequest, db: DbSession, foreman: Foreman
) -> WorkOrderOut:
    """Foreman rejects a PENDING work order, recording why."""
    work_order = get_pending_for_review(db, work_order_id)
    work_order.status = WorkOrderStatus.REJECTED
    work_order.reviewed_by = foreman.name
    work_order.reviewed_at = datetime.now()
    work_order.rejection_reason = body.reason
    db.commit()
    return to_out(work_order)
