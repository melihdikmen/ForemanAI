"""list_recent_rejections reads seeded foreman decisions through the read-only role."""

from __future__ import annotations

from app.tools.work_orders import list_recent_rejections


def test_seeded_rejection_is_returned_without_names() -> None:
    """PRES-2 has one seeded rejection; the model gets the decision, not the people."""
    result = list_recent_rejections("PRES-2")
    assert result["count"] >= 1
    first = result["rejections"][0]
    assert set(first) == {"title", "rejected_on", "reason"}  # no reviewed_by / created_by
    assert "vardiya" in first["reason"]


def test_reason_is_tagged_as_untrusted_data() -> None:
    """Free text typed by a foreman is wrapped like fault records, with the notice."""
    result = list_recent_rejections("PRES-2")
    assert result["rejections"][0]["reason"].startswith("<rejection_reason>")
    assert result["notice"]


def test_machine_without_rejections_is_empty() -> None:
    """No seeded rejections for ROBOT-1 -> empty list, no notice."""
    result = list_recent_rejections("ROBOT-1")
    assert result["count"] == 0
    assert result["rejections"] == []
    assert result["notice"] is None


def test_limit_is_capped() -> None:
    """A huge limit must not hand unbounded text to the model."""
    assert list_recent_rejections("PRES-2", limit=500)["count"] <= 10
