"""Django-side MCP client wrapper.

Lets the Groq Sales Worker call tools exposed by the standalone
`mcp_host/server.py` process over stdio, without the worker (or the LangGraph
graph) needing to know anything about the MCP protocol.

`langchain-mcp-adapters` isn't used here: it pins `mcp<2.0.0`, but this
server depends on `mcp.server.MCPServer`, an API that only exists at/after
`mcp==2.0.0`. The bridge below is hand-rolled against `mcp.ClientSession`
directly instead, avoiding that conflict.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT_PATH = Path(__file__).resolve().parent / "server.py"


@asynccontextmanager
async def mcp_session():
    """Spawn the OpsNexus MCP server over stdio and yield an initialized session.

    The subprocess and session both close when the `async with` block exits --
    any LangChain tools built from this session must be used before then.
    """
    params = StdioServerParameters(
        command=sys.executable, args=[str(SERVER_SCRIPT_PATH)]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def build_mcp_tools(session: ClientSession) -> list[Any]:
    """List the MCP server's tools and wrap each as a LangChain `@tool`."""
    from langchain_core.tools import tool

    tools_result = await session.list_tools()
    tools = []

    for mcp_tool in tools_result.tools:

        def make_tool(name: str, description: str):
            @tool(name, description=description)
            async def _call(**kwargs) -> str:
                result = await session.call_tool(name, kwargs or {})
                return "\n".join(
                    block.text for block in result.content if hasattr(block, "text")
                )

            return _call

        tools.append(make_tool(mcp_tool.name, mcp_tool.description or mcp_tool.name))

    return tools
