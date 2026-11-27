"""The MCP server must publish exactly the agent's tools, with correct read-only hints."""

from __future__ import annotations

import asyncio

from app.agent.tools import TOOL_FUNCTIONS
from app.mcp_server import READ_ONLY_TOOLS, server


def test_mcp_publishes_every_agent_tool() -> None:
    """Tool names over MCP are the same set the in-process agent uses."""
    tools = asyncio.run(server.list_tools())
    assert {tool.name for tool in tools} == set(TOOL_FUNCTIONS)


def test_read_only_hints_match_tool_design() -> None:
    """Only the three data-reading tools are marked read-only; drafting is not."""
    tools = {tool.name: tool for tool in asyncio.run(server.list_tools())}
    for name, tool in tools.items():
        assert tool.annotations is not None
        assert tool.annotations.read_only_hint is (name in READ_ONLY_TOOLS)
    assert tools["draft_work_order"].annotations.read_only_hint is False


def test_parameter_schemas_come_from_type_hints() -> None:
    """The required parameters mirror the function signatures (sanity check)."""
    tools = {tool.name: tool for tool in asyncio.run(server.list_tools())}
    assert "machine_code" in tools["list_recent_faults"].input_schema["required"]
    assert "query" in tools["search_manuals"].input_schema["required"]
