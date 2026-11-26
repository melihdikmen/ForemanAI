"""Tests for work-order drafting and how drafts are surfaced from the agent loop (no LLM)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agent.loop import _collect_draft, _run_tool
from app.tools.work_orders import WorkOrderDraft, draft_work_order

DRAFT_ARGUMENTS = {
    "machine_code": "PRES-3",
    "title": "Conta değişimi",
    "description": "Silindir altında yağ sızıntısı.",
    "proposed_actions": "LOTO, conta değişimi, sızdırmazlık testi.",
    "priority": "high",
}


def test_draft_is_valid_submit_body() -> None:
    """The tool's output validates as a WorkOrderDraft (= the POST /work-orders body)."""
    result = draft_work_order(**DRAFT_ARGUMENTS)
    assert result["status"] == "draft"
    assert WorkOrderDraft.model_validate(result).priority == "high"


def test_invalid_priority_is_rejected() -> None:
    """An unknown priority fails loudly instead of producing a bad draft."""
    with pytest.raises(ValueError):
        draft_work_order(**{**DRAFT_ARGUMENTS, "priority": "urgent"})


def test_title_too_long_is_rejected() -> None:
    """Field limits on the draft match the database column (200 chars)."""
    with pytest.raises(ValidationError):
        draft_work_order(**{**DRAFT_ARGUMENTS, "title": "x" * 201})


def test_successful_draft_is_collected() -> None:
    """A successful draft_work_order call ends up in the drafts list."""
    drafts: list[WorkOrderDraft] = []
    result = draft_work_order(**DRAFT_ARGUMENTS)
    _collect_draft("draft_work_order", result, drafts)
    assert [draft.machine_code for draft in drafts] == ["PRES-3"]


def test_failed_draft_and_other_tools_are_ignored() -> None:
    """Tool errors and non-draft tools never produce a draft."""
    drafts: list[WorkOrderDraft] = []
    failed = _run_tool("draft_work_order", '{"machine_code": "PRES-3"}')  # missing args
    assert "error" in failed
    _collect_draft("draft_work_order", failed, drafts)
    _collect_draft("get_fault_history", {"total": 3}, drafts)
    assert drafts == []
