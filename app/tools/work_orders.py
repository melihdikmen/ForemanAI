"""Work-order drafting tool. Produces a DRAFT only — it never writes to the database.

Persisting a work order happens only after foreman approval (phase 5). Keeping this
tool write-free is a deliberate safety boundary (the assistant cannot change state).
"""

from __future__ import annotations

from typing import Any


def draft_work_order(
    machine_code: str,
    title: str,
    description: str,
    proposed_actions: str,
    priority: str = "medium",
) -> dict[str, Any]:
    """Build a work-order DRAFT for foreman review. Does not save anything."""
    return {
        "status": "draft",
        "machine_code": machine_code,
        "title": title,
        "description": description,
        "proposed_actions": proposed_actions,
        "priority": priority,
        "note": "Bu bir taslaktır; ustabaşı onayı olmadan kaydedilmez.",
    }
