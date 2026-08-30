from unittest.mock import AsyncMock, patch

import pytest

from mcp_host.client import SERVER_SCRIPT_PATH, build_mcp_tools, mcp_session


class _FakeBlock:
    def __init__(self, text: str):
        self.text = text


class _FakeNonTextBlock:
    pass


class _FakeToolInfo:
    def __init__(self, name: str, description: str | None = None):
        self.name = name
        self.description = description


class _FakeListToolsResult:
    def __init__(self, tools):
        self.tools = tools


class _FakeCallToolResult:
    def __init__(self, content):
        self.content = content


@pytest.mark.asyncio
async def test_mcp_session_context_manager():
    fake_client_instance = AsyncMock()

    class FakeClientContext:
        def __init__(self, transport):
            self.transport = transport

        async def __aenter__(self):
            return fake_client_instance

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    with (
        patch("mcp_host.client.StdioServerParameters") as MockParams,
        patch(
            "mcp_host.client.stdio_client", return_value="fake_transport"
        ) as mock_stdio,
        patch(
            "mcp_host.client.Client", side_effect=FakeClientContext
        ) as MockClientClass,
    ):
        async with mcp_session() as client:
            assert client is fake_client_instance

        MockParams.assert_called_once()
        _, kwargs = MockParams.call_args
        assert kwargs["args"] == [str(SERVER_SCRIPT_PATH)]
        mock_stdio.assert_called_once()
        MockClientClass.assert_called_once_with("fake_transport")


@pytest.mark.asyncio
async def test_build_mcp_tools_constructs_langchain_tools():
    tool_info_1 = _FakeToolInfo(
        name="get_internal_pricing_policy",
        description="Return internal pricing policy JSON.",
    )
    tool_info_2 = _FakeToolInfo(
        name="get_compliance_guidelines",
        description=None,
    )

    mock_client = AsyncMock()
    mock_client.list_tools.return_value = _FakeListToolsResult(
        tools=[tool_info_1, tool_info_2]
    )

    call_result_1 = _FakeCallToolResult(
        content=[_FakeBlock("Line 1"), _FakeBlock("Line 2")]
    )
    call_result_2 = _FakeCallToolResult(
        content=[_FakeBlock("Compliance text"), _FakeNonTextBlock()]
    )

    def call_tool_side_effect(name, kwargs):
        if name == "get_internal_pricing_policy":
            return call_result_1
        return call_result_2

    mock_client.call_tool.side_effect = call_tool_side_effect

    tools = await build_mcp_tools(mock_client)
    assert len(tools) == 2

    # Check first tool
    tool_1 = tools[0]
    assert tool_1.name == "get_internal_pricing_policy"
    assert tool_1.description == "Return internal pricing policy JSON."

    res_1 = await tool_1.ainvoke({"tier": "enterprise"})
    assert res_1 == "Line 1\nLine 2"
    assert mock_client.call_tool.called
    first_call_args = mock_client.call_tool.call_args_list[0]
    assert first_call_args[0][0] == "get_internal_pricing_policy"

    # Check second tool with fallback description
    tool_2 = tools[1]
    assert tool_2.name == "get_compliance_guidelines"
    assert tool_2.description == "get_compliance_guidelines"

    res_2 = await tool_2.ainvoke({})
    assert res_2 == "Compliance text"
    second_call_args = mock_client.call_tool.call_args_list[1]
    assert second_call_args[0][0] == "get_compliance_guidelines"


@pytest.mark.asyncio
async def test_build_mcp_tools_with_empty_tools():
    mock_client = AsyncMock()
    mock_client.list_tools.return_value = _FakeListToolsResult(tools=[])

    tools = await build_mcp_tools(mock_client)
    assert tools == []
