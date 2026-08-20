"""Stubbed centralized registry for agent tools.

Week 6: `register()` will accept real LangChain `BaseTool` / MCP tool
objects (e.g. wrapping `mcp_host`'s tools and `memory.ChromaDBClient`
methods), collected here once at startup, then handed to the LangGraph
Supervisor/Worker agents as their available tool set -- so agent
construction never has to know where a tool came from.
"""

from typing import Any


class ToolRegistry:
    """In-memory name -> tool lookup, populated before LangGraph agent construction."""

    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}

    def register(self, name: str, tool: Any) -> None:
        self._tools[name] = tool

    def get(self, name: str) -> Any:
        return self._tools[name]

    def all(self) -> dict[str, Any]:
        return dict(self._tools)
