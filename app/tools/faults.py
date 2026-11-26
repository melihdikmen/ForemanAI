"""Read-only fault-history tool for the agent.

Deliberately NOT raw SQL: the agent passes filters, we run a fixed read-only query
and return a compact summary (totals + breakdowns). It never writes to the database.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import FaultRecord, Machine, Severity


def get_fault_history(
    machine_code: str | None = None,
    since_months: int | None = None,
    alarm_code: str | None = None,
    severity: str | None = None,
) -> dict[str, Any]:
    """Summarize fault records matching the filters (read-only).

    Args:
        machine_code: limit to one machine, e.g. "PRES-3" (None = all machines).
        since_months: only faults in the last N months (None = all time).
        alarm_code: limit to one alarm code, e.g. "E-102".
        severity: one of low/medium/high/critical.

    Returns totals and breakdowns so the agent can answer counting/aggregation questions.
    """
    conditions = []
    if machine_code:
        conditions.append(Machine.code == machine_code)
    if since_months is not None:
        conditions.append(
            FaultRecord.occurred_at >= datetime.now() - timedelta(days=30 * since_months)
        )
    if alarm_code:
        conditions.append(FaultRecord.alarm_code == alarm_code)
    if severity:
        conditions.append(FaultRecord.severity == Severity(severity.lower()))

    with SessionLocal() as session:

        def filtered(*columns):
            """A SELECT over the fault/machine join with the shared filters applied."""
            return (
                select(*columns)
                .select_from(FaultRecord)
                .join(Machine, Machine.id == FaultRecord.machine_id)
                .where(*conditions)
            )

        total = session.scalar(filtered(func.count())) or 0
        downtime = session.scalar(
            filtered(func.coalesce(func.sum(FaultRecord.downtime_minutes), 0))
        )
        by_machine = session.execute(
            filtered(Machine.code, func.count())
            .group_by(Machine.code)
            .order_by(func.count().desc())
        ).all()
        by_severity = session.execute(
            filtered(FaultRecord.severity, func.count()).group_by(FaultRecord.severity)
        ).all()
        by_alarm = session.execute(
            filtered(FaultRecord.alarm_code, func.count())
            .group_by(FaultRecord.alarm_code)
            .order_by(func.count().desc())
            .limit(5)
        ).all()

    return {
        "filters": {
            "machine_code": machine_code,
            "since_months": since_months,
            "alarm_code": alarm_code,
            "severity": severity,
        },
        "total_count": total,
        "total_downtime_minutes": int(downtime or 0),
        "by_machine": {code: count for code, count in by_machine},
        "by_severity": {str(sev): count for sev, count in by_severity},
        "top_alarm_codes": {code: count for code, count in by_alarm},
    }
