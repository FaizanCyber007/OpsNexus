import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from orchestration.graph import (
    ClassificationResult,
    SalesWorkerError,
    StructuredAnswer,
    _extract_tool_calls,
    _route_after_supervisor,
    sales_worker_node,
    supervisor_node,
)


def test_route_after_supervisor_sends_sales_rfp_to_worker():
    assert _route_after_supervisor({"route": "sales_rfp"}) == "sales_worker"


@pytest.mark.parametrize(
    "route", ["invoice_reconciliation", "compliance_audit", "general_intake"]
)
def test_route_after_supervisor_ends_for_other_routes(route):
    assert _route_after_supervisor({"route": route}) == "__end__"


class TestExtractToolCalls:
    def test_pairs_tool_calls_with_their_results_in_order(self):
        messages = [
            HumanMessage(content="hi"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call_1",
                        "name": "search_company_knowledge",
                        "args": {"query": "pricing"},
                    }
                ],
            ),
            ToolMessage(
                content="No relevant prior context found.", tool_call_id="call_1"
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "call_2", "name": "get_internal_pricing_policy", "args": {}}
                ],
            ),
            ToolMessage(content='{"tiers": []}', tool_call_id="call_2"),
            AIMessage(content="final answer text"),
        ]

        result = _extract_tool_calls(messages)

        assert result == [
            {
                "tool_name": "search_company_knowledge",
                "input": {"query": "pricing"},
                "output": "No relevant prior context found.",
            },
            {
                "tool_name": "get_internal_pricing_policy",
                "input": {},
                "output": '{"tiers": []}',
            },
        ]

    def test_no_tool_calls_returns_empty_list(self):
        messages = [HumanMessage(content="hi"), AIMessage(content="just an answer")]

        assert _extract_tool_calls(messages) == []

    def test_unmatched_tool_message_is_ignored(self):
        messages = [ToolMessage(content="orphaned", tool_call_id="unknown_call")]

        assert _extract_tool_calls(messages) == []


class TestSupervisorNode:
    def test_returns_route_and_reasoning_from_llm(self):
        canned = ClassificationResult(
            route="invoice_reconciliation", reasoning="Mentions line items and totals."
        )
        fake_llm = MagicMock()
        fake_llm.with_structured_output.return_value.ainvoke = AsyncMock(
            return_value=canned
        )

        with patch("orchestration.graph.LLMFactory") as MockFactory:
            MockFactory.return_value.get_supervisor_llm.return_value = fake_llm

            result = asyncio.run(
                supervisor_node({"document_text": "Invoice #1: $500 due."})
            )

        assert result == {
            "route": "invoice_reconciliation",
            "reasoning": "Mentions line items and totals.",
        }

    def test_empty_document_text_still_invokes_llm(self):
        canned = ClassificationResult(route="general_intake", reasoning="No content.")
        fake_llm = MagicMock()
        fake_llm.with_structured_output.return_value.ainvoke = AsyncMock(
            return_value=canned
        )

        with patch("orchestration.graph.LLMFactory") as MockFactory:
            MockFactory.return_value.get_supervisor_llm.return_value = fake_llm
            result = asyncio.run(supervisor_node({"document_text": ""}))

        assert result["route"] == "general_intake"
        call_args = fake_llm.with_structured_output.return_value.ainvoke.call_args
        assert "(empty document)" in call_args.args[0][1][1]


class TestSalesWorkerNode:
    @asynccontextmanager
    async def _fake_mcp_session(self):
        yield object()

    def test_wraps_agent_failure_in_sales_worker_error(self):
        with (
            patch("mcp_host.client.mcp_session", self._fake_mcp_session),
            patch("mcp_host.client.build_mcp_tools", AsyncMock(return_value=[])),
            patch(
                "orchestration.graph._run_sales_worker_agent",
                AsyncMock(side_effect=TimeoutError("groq timed out")),
            ),
            patch(
                "orchestration.graph.build_search_company_knowledge_tool",
                return_value="search_tool",
            ),
        ):
            with pytest.raises(SalesWorkerError, match="groq timed out"):
                asyncio.run(
                    sales_worker_node(
                        {"organization_id": "org-1", "document_text": "hi"}
                    )
                )

    def test_falls_back_gracefully_when_mcp_session_unavailable(self):
        @asynccontextmanager
        async def broken_session():
            raise ConnectionError("mcp unreachable")
            yield  # pragma: no cover

        fake_answer = StructuredAnswer(
            content="answer without mcp", confidence_score=0.4
        )

        with (
            patch("mcp_host.client.mcp_session", broken_session),
            patch(
                "orchestration.graph._run_sales_worker_agent",
                AsyncMock(return_value=(fake_answer, [])),
            ) as mock_run,
            patch(
                "orchestration.graph.build_search_company_knowledge_tool",
                return_value="search_tool",
            ),
        ):
            result = asyncio.run(
                sales_worker_node({"organization_id": "org-1", "document_text": "hi"})
            )

        assert result == {"answer": fake_answer, "worker_tool_calls": []}
        # Only the search tool was passed -- MCP tools never got added.
        assert mock_run.call_args.args[1] == ["search_tool"]

    def test_uses_mcp_tools_when_available(self):
        fake_answer = StructuredAnswer(content="answer with mcp", confidence_score=0.9)

        with (
            patch("mcp_host.client.mcp_session", self._fake_mcp_session),
            patch(
                "mcp_host.client.build_mcp_tools",
                AsyncMock(return_value=["pricing_tool"]),
            ),
            patch(
                "orchestration.graph._run_sales_worker_agent",
                AsyncMock(return_value=(fake_answer, [])),
            ) as mock_run,
            patch(
                "orchestration.graph.build_search_company_knowledge_tool",
                return_value="search_tool",
            ),
        ):
            result = asyncio.run(
                sales_worker_node({"organization_id": "org-1", "document_text": "hi"})
            )

        assert result == {"answer": fake_answer, "worker_tool_calls": []}
        assert mock_run.call_args.args[1] == ["search_tool", "pricing_tool"]

    def test_propagates_extracted_worker_tool_calls(self):
        fake_answer = StructuredAnswer(content="answer", confidence_score=0.7)
        fake_tool_calls = [
            {
                "tool_name": "search_company_knowledge",
                "input": {"query": "pricing"},
                "output": "No relevant prior context found.",
            }
        ]

        with (
            patch("mcp_host.client.mcp_session", self._fake_mcp_session),
            patch("mcp_host.client.build_mcp_tools", AsyncMock(return_value=[])),
            patch(
                "orchestration.graph._run_sales_worker_agent",
                AsyncMock(return_value=(fake_answer, fake_tool_calls)),
            ),
            patch(
                "orchestration.graph.build_search_company_knowledge_tool",
                return_value="search_tool",
            ),
        ):
            result = asyncio.run(
                sales_worker_node({"organization_id": "org-1", "document_text": "hi"})
            )

        assert result == {"answer": fake_answer, "worker_tool_calls": fake_tool_calls}
