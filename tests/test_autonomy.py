"""The code must match the autonomy table in RESPONSIBLE_AI.md.

If a new tool is added, this test fails on purpose: the table has to be updated and the
tool's autonomy level argued before the agent gets it.
"""

from __future__ import annotations

import inspect

import app.tools.faults
import app.tools.manuals
import app.tools.work_orders
from app.agent.tools import TOOL_FUNCTIONS
from app.tools.work_orders import draft_work_order

# Level L3 (read within bounds) and L1 (suggest) tools from RESPONSIBLE_AI.md §2.
READ_TOOLS = {"search_manuals", "get_fault_history", "list_recent_faults", "list_recent_rejections"}
SUGGEST_TOOLS = {"draft_work_order"}

# Capabilities that must not exist at all (L0): anything that could send data outside.
FORBIDDEN_IMPORTS = ("httpx", "requests", "smtplib", "urllib.request", "aiohttp")


def test_agent_tools_are_exactly_the_documented_set() -> None:
    """No undocumented tool reaches the model."""
    assert set(TOOL_FUNCTIONS) == READ_TOOLS | SUGGEST_TOOLS


def test_the_only_non_read_tool_returns_a_draft() -> None:
    """draft_work_order is L1: it proposes, it does not persist."""
    result = draft_work_order(
        machine_code="PRES-1",
        title="Test",
        description="Test",
        proposed_actions="LOTO, then inspect",
        priority="low",
    )
    assert result["status"] == "draft"


def test_tool_modules_have_no_outbound_channel() -> None:
    """L0: no tool module imports an HTTP or mail client (lethal trifecta, third leg)."""
    for module in (app.tools.faults, app.tools.manuals, app.tools.work_orders):
        source = inspect.getsource(module)
        for name in FORBIDDEN_IMPORTS:
            assert f"import {name}" not in source and f"from {name}" not in source, (
                f"{module.__name__} imports {name}"
            )
