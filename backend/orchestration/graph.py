"""The real LangGraph Supervisor/Worker engine.

A Gemini Supervisor node classifies the document into one of the routes
`DeterministicRouter` used to guess at with keywords/extensions. Only the
`sales_rfp` route gets a real Worker so far: a Groq-powered LangGraph ReAct
agent equipped with the `search_company_knowledge` tool, whose final output is
strictly typed via `StructuredAnswer` (Pydantic) rather than free text.

Other routes are left for `agent_runner` to fall back to the existing
deterministic mock pipeline -- this graph only owns classification + the Sales
Worker.
"""

import logging
from typing import Any, TypedDict

from orchestration.model_client import LLMConfigurationError, LLMFactory
from orchestration.schemas import ClassificationResult, StructuredAnswer
from orchestration.tool_registry import build_search_company_knowledge_tool

logger = logging.getLogger(__name__)


class SalesWorkerError(Exception):
    """Raised when the Sales Worker (Groq) fails to produce an answer, after
    the Supervisor has already classified the document as sales_rfp. Distinct
    from an MCP-server-unavailable condition, which is handled separately and
    gracefully -- this represents a real, user-visible failure."""


# Keep prompts within a safe token budget regardless of document size.
MAX_DOCUMENT_CHARS = 8000

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Agent for OpsNexus, a \
B2B document-intake platform. Classify the incoming document into exactly \
one route:

- sales_rfp: sales RFPs, security questionnaires, vendor onboarding forms
- invoice_reconciliation: invoices, billing statements, ledger entries
- compliance_audit: SOC2/compliance logs, audit reports, policy documents
- general_intake: anything that doesn't clearly fit the above

Base your decision on the document content, not just its filename."""

SALES_WORKER_SYSTEM_PROMPT = """You are the Sales Worker Agent for OpsNexus. \
You have been handed a sales RFP or security questionnaire. Read it \
carefully, use the `search_company_knowledge` tool to find relevant prior \
answers or policies from this organization's history, and synthesize a \
concise, accurate draft response. If no relevant prior context exists, say \
so plainly rather than inventing facts, and lower your confidence score \
accordingly. Also identify any concrete risks (e.g. missing compliance \
documentation, contractual red flags) and concrete next-step action items \
a human reviewer should take before this response goes out."""


class GraphState(TypedDict):
    organization_id: str
    document_text: str
    route: str
    reasoning: str
    answer: StructuredAnswer | None
    worker_tool_calls: list[dict[str, Any]]


async def supervisor_node(state: GraphState) -> dict:
    llm = LLMFactory().get_supervisor_llm().with_structured_output(ClassificationResult)
    document_excerpt = state["document_text"][:MAX_DOCUMENT_CHARS] or "(empty document)"

    result: ClassificationResult = await llm.ainvoke(
        [
            ("system", SUPERVISOR_SYSTEM_PROMPT),
            ("user", f"Document content:\n\n{document_excerpt}"),
        ]
    )
    return {"route": result.route, "reasoning": result.reasoning}


def _extract_tool_calls(messages: list) -> list[dict[str, Any]]:
    """Extract each real tool invocation from a ReAct agent's message history.

    LangGraph's `create_react_agent` never persists its intermediate tool
    calls anywhere -- they only exist in this in-memory message list. Walk
    it, pairing each `AIMessage.tool_calls` entry with the `ToolMessage` that
    answers it (matched by `tool_call_id`), so the caller can persist a real
    `ToolCall` row per step instead of losing this trail once the node
    returns.
    """
    from langchain_core.messages import ToolMessage

    pending_by_id: dict[str, dict[str, Any]] = {}
    extracted: list[dict[str, Any]] = []

    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            pending_by_id[call["id"]] = {
                "tool_name": call["name"],
                "input": call["args"],
            }

        if isinstance(message, ToolMessage):
            pending = pending_by_id.get(message.tool_call_id)
            if pending is not None:
                extracted.append({**pending, "output": message.content})

    return extracted


async def _run_sales_worker_agent(
    document_excerpt: str, tools: list
) -> tuple[StructuredAnswer, list[dict[str, Any]]]:
    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(
        model=LLMFactory().get_worker_llm(),
        tools=tools,
        prompt=SALES_WORKER_SYSTEM_PROMPT,
        response_format=StructuredAnswer,
    )
    result = await agent.ainvoke(
        {
            "messages": [
                (
                    "user",
                    f"Document content:\n\n{document_excerpt}\n\n"
                    "Draft a response to this RFP/questionnaire.",
                )
            ]
        }
    )
    return result["structured_response"], _extract_tool_calls(result["messages"])


async def sales_worker_node(state: GraphState) -> dict:
    from contextlib import AsyncExitStack

    from mcp_host.client import build_mcp_tools, mcp_session

    search_tool = build_search_company_knowledge_tool(state["organization_id"])
    document_excerpt = state["document_text"][:MAX_DOCUMENT_CHARS] or "(empty document)"

    tools = [search_tool]
    worker_error: Exception | None = None
    llm_config_error: LLMConfigurationError | None = None
    answer = None
    worker_tool_calls: list[dict[str, Any]] = []

    # Any raise below happens *after* this block exits, not from inside it:
    # an exception raised while the MCP session's underlying anyio task
    # group is still open gets wrapped in a BaseExceptionGroup by the time it
    # reaches the caller, so a bare `except SalesWorkerError`/
    # `except LLMConfigurationError` in agent_runner.py would never match it.
    # Closing the stack first (the async with body only records which
    # exception happened) guarantees a plain, matchable exception propagates.
    async with AsyncExitStack() as stack:
        try:
            session = await stack.enter_async_context(mcp_session())
            tools = [search_tool, *await build_mcp_tools(session)]
        except Exception:
            logger.warning(
                "MCP server unavailable; Sales Worker running without MCP tools",
                exc_info=True,
            )

        try:
            answer, worker_tool_calls = await _run_sales_worker_agent(
                document_excerpt, tools
            )
        except LLMConfigurationError as exc:
            # Missing GROQ_API_KEY is a configuration problem, not a Worker
            # failure -- agent_runner.py has its own dedicated fallback path
            # for this exact exception type, so it must reach it unwrapped.
            llm_config_error = exc
        except Exception as exc:
            worker_error = exc

    if llm_config_error is not None:
        raise llm_config_error
    if worker_error is not None:
        raise SalesWorkerError(str(worker_error)) from worker_error

    return {"answer": answer, "worker_tool_calls": worker_tool_calls}


def _route_after_supervisor(state: GraphState) -> str:
    return "sales_worker" if state["route"] == "sales_rfp" else "__end__"


def build_graph():
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(GraphState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("sales_worker", sales_worker_node)
    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {"sales_worker": "sales_worker", "__end__": END},
    )
    workflow.add_edge("sales_worker", END)
    return workflow.compile()


graph = build_graph()
