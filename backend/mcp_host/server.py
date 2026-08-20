"""Standalone MCP server skeleton for OpsNexus.

Runs outside the Django request/response cycle -- this process exposes
OpsNexus resources/tools to MCP-compatible clients (e.g. the future
Supervisor Agent) over its own transport.
"""

from mcp.server import MCPServer

mcp = MCPServer("opsnexus-mcp-host")


@mcp.resource("opsnexus://documents/schema")
def mock_resource() -> str:
    """Placeholder resource stub."""
    return ""


@mcp.tool()
def mock_tool() -> None:
    """Placeholder tool stub."""
    pass


if __name__ == "__main__":
    mcp.run()
