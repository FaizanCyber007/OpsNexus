"""Django-side MCP client wrapper.

Lets the Groq Sales Worker call tools exposed by the standalone
`mcp_host/server.py` process over stdio, without the worker (or the LangGraph
graph) needing to know anything about the MCP protocol.

Uses `mcp.client.client.Client`, the installed `mcp==2.0.0` SDK's high-level
client -- it accepts any object satisfying the `Transport` protocol directly
(an async context manager yielding read/write streams), which `stdio_client`
already is, and handles the session handshake internally. No explicit
`ClientSession` construction or `session.initialize()` call is needed.

`langchain-mcp-adapters` isn't used here: it pins `mcp<2.0.0`, but this
server depends on `mcp.server.MCPServer`, an API that only exists at/after
`mcp==2.0.0`. The bridge below is hand-rolled instead, avoiding that conflict.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp.client.client import Client
from mcp.client.stdio import StdioServerParameters, stdio_client

SERVER_SCRIPT_PATH = Path(__file__).resolve().parent / "server.py"


@asynccontextmanager
async def mcp_session():
    """Spawn the OpsNexus MCP server over stdio and yield a ready client.

    The subprocess and client both close when the `async with` block exits --
    any LangChain tools built from this client must be used before then.
    """
    params = StdioServerParameters(
        command=sys.executable, args=[str(SERVER_SCRIPT_PATH)]
    )
    async with Client(stdio_client(params)) as client:
        yield client


async def build_mcp_tools(client: Client) -> list[Any]:
    """List the MCP server's tools and wrap each as a LangChain `@tool`."""
    from langchain_core.tools import tool

    tools_result = await client.list_tools()
    tools = []

    for mcp_tool in tools_result.tools:

        def make_tool(name: str, description: str):
            @tool(name, description=description)
            async def _call(**kwargs) -> str:
                result = await client.call_tool(name, kwargs or {})
                return "\n".join(
                    block.text for block in result.content if hasattr(block, "text")
                )

            return _call

        tools.append(make_tool(mcp_tool.name, mcp_tool.description or mcp_tool.name))

    return tools
