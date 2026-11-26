"""SQLAlchemy ORM models: machines, fault records, work orders."""

from __future__ import annotations

import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.embedding import EMBEDDING_DIM


class Severity(enum.StrEnum):
    """How serious a fault was."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkOrderStatus(enum.StrEnum):
    """Lifecycle of a work order; nothing is persisted as 'approved' without a foreman."""

    DRAFT = "draft"  # created by the assistant, not yet submitted
    PENDING = "pending"  # waiting for foreman review
    APPROVED = "approved"  # foreman approved
    REJECTED = "rejected"  # foreman rejected


class Priority(enum.StrEnum):
    """How urgently a work order should be handled."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Machine(Base):
    """A physical machine on the shop floor (e.g. a hydraulic press)."""

    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # e.g. "PRES-3"
    name: Mapped[str] = mapped_column(String(100))
    machine_type: Mapped[str] = mapped_column(String(50))
    location: Mapped[str] = mapped_column(String(100))
    manufacturer: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    installed_at: Mapped[datetime]

    # Back-references: Python-side conveniences, not database columns.
    fault_records: Mapped[list[FaultRecord]] = relationship(back_populates="machine")
    work_orders: Mapped[list[WorkOrder]] = relationship(back_populates="machine")


class FaultRecord(Base):
    """A historical fault/breakdown record, used for RAG and SQL queries."""

    __tablename__ = "fault_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(index=True)
    alarm_code: Mapped[str | None] = mapped_column(String(20), index=True)  # e.g. "E-204"
    symptom: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str] = mapped_column(Text)
    action_taken: Mapped[str] = mapped_column(Text)
    severity: Mapped[Severity] = mapped_column(Enum(Severity, native_enum=False), index=True)
    downtime_minutes: Mapped[int]
    technician_name: Mapped[str] = mapped_column(String(100))

    machine: Mapped[Machine] = relationship(back_populates="fault_records")


class WorkOrder(Base):
    """A maintenance work order. Created as a draft; only persisted as approved by a foreman."""

    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(index=True)
    created_by: Mapped[str] = mapped_column(String(100))  # technician who requested it
    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus, native_enum=False),
        default=WorkOrderStatus.DRAFT,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    proposed_actions: Mapped[str] = mapped_column(Text)
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, native_enum=False),
        default=Priority.MEDIUM,
    )
    approved_by: Mapped[str | None] = mapped_column(String(100))  # foreman, set on approval
    approved_at: Mapped[datetime | None]

    machine: Mapped[Machine] = relationship(back_populates="work_orders")


class ManualChunk(Base):
    """One heading-based chunk of a manual plus its embedding, for RAG retrieval."""

    __tablename__ = "manual_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_code: Mapped[str] = mapped_column(String(20), index=True)  # e.g. "PRES-3"
    source: Mapped[str] = mapped_column(String(100))  # file name, e.g. "PRES-3.md"
    section: Mapped[str] = mapped_column(String(200))  # heading text
    content: Mapped[str] = mapped_column(Text)  # embedded text (title + heading + body)
    alarm_codes: Mapped[str | None] = mapped_column(String(200))  # comma-joined, e.g. "E-101,E-102"
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
