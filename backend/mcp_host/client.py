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
    from mcp.types import TextContent

    tools_result = await client.list_tools()
    tools = []

    for mcp_tool in tools_result.tools:
        name = mcp_tool.name
        description = mcp_tool.description or name
        input_schema = getattr(mcp_tool, "input_schema", None) or getattr(
            mcp_tool, "inputSchema", None
        )

        def make_tool(t_name: str, t_description: str, t_schema: Any):
            tool_kwargs: dict[str, Any] = {"description": t_description}
            if (
                t_schema is not None
                and isinstance(t_schema, dict)
                and t_schema.get("properties")
            ):
                tool_kwargs["args_schema"] = t_schema

            @tool(t_name, **tool_kwargs)
            async def _call(**kwargs) -> str:
                result = await client.call_tool(t_name, kwargs or {})
                is_error = getattr(result, "is_error", False) or getattr(
                    result, "isError", False
                )
                text_blocks = [
                    block.text
                    for block in result.content
                    if isinstance(block, TextContent)
                    or (
                        hasattr(block, "text")
                        and getattr(block, "type", "text") == "text"
                    )
                ]
                output = "\n".join(text_blocks)
                if is_error:
                    err_text = output or "Tool execution failed"
                    raise RuntimeError(
                        f"MCP tool '{t_name}' returned an error: {err_text}"
                    )
                return output

            return _call

        tools.append(make_tool(name, description, input_schema))

    return tools
