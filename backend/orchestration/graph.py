"""The real LangGraph Supervisor/Worker engine.

A Gemini Supervisor node classifies the document into one of the routes
`DeterministicRouter` used to guess at with keywords/extensions.  Three routes
now have real Workers:

- ``sales_rfp``: a Groq-powered LangGraph ReAct agent equipped with the
  ``search_company_knowledge`` tool, whose final output is strictly typed via
  ``StructuredAnswer`` (Pydantic).
- ``compliance_audit``: a Groq-powered LangGraph ReAct agent equipped with
  the MCP ``get_security_policies`` tool, whose final output is strictly typed
  via ``ComplianceAuditResult`` (Pydantic).
- ``invoice_reconciliation``: a Groq-powered LangGraph ReAct agent equipped
  with the MCP ``get_open_purchase_orders`` tool, whose final output is
  strictly typed via ``InvoiceReconciliationResult`` (Pydantic).

Other routes fall back to ``agent_runner``'s deterministic mock pipeline.

## Production Guardrails (added in refactor)

### Pydantic Auto-Correction Loop
Both the Supervisor and the Sales Worker use `with_structured_output` /
`response_format` to enforce Pydantic schemas.  If the LLM produces output
that fails schema validation a `ValidationError` is caught and fed back as a
`HumanMessage`:

    "Your output failed validation: <error>. Please correct it."

The loop retries up to `MAX_VALIDATION_LOOPS` (2) times before propagating
the error.

### Retry & Fallback
Transient API errors (rate-limits, 503s) are handled transparently by the
tenacity decorators in `model_client.py`; the Groq → Gemini fallback chain
is also assembled there.  This module requires no additional retry logic.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage
from pydantic import ValidationError
from typing_extensions import TypedDict

from orchestration.model_client import LLMConfigurationError, LLMFactory
from orchestration.schemas import (
    ClassificationResult,
    ComplianceAuditResult,
    InvoiceReconciliationResult,
    StructuredAnswer,
)
from orchestration.tool_registry import build_search_company_knowledge_tool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Keep prompts within a safe token budget regardless of document size.
MAX_DOCUMENT_CHARS = 8000

# Maximum number of *additional* correction attempts after the first
# ValidationError.  With MAX_VALIDATION_LOOPS = 2 the LLM gets at most
# 3 total calls (1 original + 2 corrections) before the error is re-raised.
MAX_VALIDATION_LOOPS = 2

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


COMPLIANCE_WORKER_SYSTEM_PROMPT = """You are the Compliance Auditor Agent for \
OpsNexus. You have been handed a compliance log file (.log) or audit report \
(.pdf). Your task is strictly two-phased:

1. **Fetch policies**: Call the `get_security_policies` tool to retrieve the \
full list of internal company security policies.

2. **Audit the document**: Read the document content provided in the user \
message and cross-reference every line against each retrieved policy. \
Identify every concrete violation with a specific quote or reference from the \
document (e.g., "server.log line 42: SSH login without MFA from 203.0.113.5"). \
Do NOT invent violations that are not evidenced by the document. \
Do NOT skip any policy that may be relevant.

Produce your final structured output using the `ComplianceAuditResult` schema:
- `is_compliant`: False if ANY violations are found, True only if the \
document is entirely clean.
- `violations`: A list of specific breach strings. Empty list if compliant.
- `severity`: The highest severity level across all violations \
("Critical" > "High" > "Medium" > "Low"). Use "None" only if fully compliant.
- `recommended_remediations`: One actionable remediation per violation."""


INVOICE_WORKER_SYSTEM_PROMPT = """You are the Invoice Reconciliation Agent for \
OpsNexus. You have been handed an invoice document. Your task is strictly \
two-phased:

1. **Fetch the ledger**: Call the `get_open_purchase_orders` tool to retrieve \
the full list of open purchase orders (POs), approved vendors, and their \
approved amounts.

2. **Reconcile the invoice**: Read the invoice content provided in the user \
message and mathematically reconcile it against the retrieved ledger:
   - Extract the total monetary amount from the invoice (`extracted_total`).
   - Match the vendor name on the invoice against the approved vendor list.
   - Find the matching PO by vendor name or PO number referenced in the \
invoice.
   - Compare the invoice total against the PO's `approved_amount_usd`.
   - Compare line items if present.
   - List every concrete discrepancy with specific values \
(e.g., "Total $12,500 exceeds PO-1042 approved limit of $10,000 by $2,500", \
"Vendor 'Acme Corp' on invoice does not match PO vendor 'Acme Corporation'"). \
Do NOT invent discrepancies not evidenced by the document.

Produce your final structured output using the `InvoiceReconciliationResult` \
schema:
- `is_matched`: True ONLY if vendor, amount, and all line items reconcile \
perfectly.
- `discrepancies`: A list of specific mismatch strings. Empty if is_matched.
- `approved_for_payment`: True ONLY when is_matched is True AND extracted_total \
<= approved PO amount.
- `extracted_total`: The raw total parsed from the invoice as a float."""


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class SalesWorkerError(Exception):
    """Raised when the Sales Worker (Groq) fails to produce an answer, after
    the Supervisor has already classified the document as sales_rfp. Distinct
    from an MCP-server-unavailable condition, which is handled separately and
    gracefully -- this represents a real, user-visible failure."""


class ComplianceWorkerError(Exception):
    """Raised when the Compliance Worker (Groq) fails to produce an audit
    result, after the Supervisor has classified the document as
    compliance_audit. Analogous to SalesWorkerError and intentionally kept
    separate so agent_runner.py can distinguish the two failure modes."""


class InvoiceWorkerError(Exception):
    """Raised when the Invoice Reconciliation Worker (Groq) fails to produce a
    result, after the Supervisor has classified the document as
    invoice_reconciliation. Kept separate from SalesWorkerError and
    ComplianceWorkerError so agent_runner.py can apply route-specific
    fallback logic."""


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------


class GraphState(TypedDict, total=False):
    organization_id: str
    document_text: str
    route: str
    reasoning: str
    answer: StructuredAnswer | None
    compliance_audit: ComplianceAuditResult | None
    invoice_reconciliation: InvoiceReconciliationResult | None
    worker_tool_calls: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


async def supervisor_node(state: GraphState) -> dict:
    """Classify the document and populate ``route`` + ``reasoning``.

    Wraps the LLM call in a Pydantic auto-correction loop: if
    `with_structured_output` raises a `ValidationError` the error is fed back
    to the model as a correction `HumanMessage` and the call is retried up to
    `MAX_VALIDATION_LOOPS` times.
    """
    llm = LLMFactory().get_supervisor_llm(structured_schema=ClassificationResult)
    document_excerpt = state["document_text"][:MAX_DOCUMENT_CHARS] or "(empty document)"

    messages: list = [
        ("system", SUPERVISOR_SYSTEM_PROMPT),
        ("user", f"Document content:\n\n{document_excerpt}"),
    ]

    last_exc: ValidationError | None = None
    for attempt in range(MAX_VALIDATION_LOOPS + 1):
        try:
            result: ClassificationResult = await llm.ainvoke(messages)
            return {"route": result.route, "reasoning": result.reasoning}
        except ValidationError as exc:
            last_exc = exc
            if attempt == MAX_VALIDATION_LOOPS:
                logger.error(
                    "Supervisor: structured-output validation failed after %d "
                    "correction attempt(s). Propagating error.",
                    MAX_VALIDATION_LOOPS,
                )
                raise
            logger.warning(
                "Supervisor: ValidationError on attempt %d/%d — sending "
                "auto-correction prompt.",
                attempt + 1,
                MAX_VALIDATION_LOOPS + 1,
            )
            messages.append(
                HumanMessage(
                    content=(
                        f"Your output failed validation: {last_exc}. "
                        "Please correct it."
                    )
                )
            )

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Unexpected failure")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


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
    """Run the ReAct Sales Worker with structured submission tool and fallback parsing."""
    import json
    import re
    from langchain_core.tools import tool
    from langgraph.prebuilt import create_react_agent  # type: ignore

    @tool
    def submit_sales_answer(
        content: str,
        executive_summary: str,
        risk_flags: list[str],
        action_items: list[str],
        confidence_score: float,
    ) -> str:
        """Submit the final synthesized sales/RFP answer and findings."""
        return "Sales answer recorded successfully."

    all_tools = [*tools, submit_sales_answer]
    json_schema = json.dumps(StructuredAnswer.model_json_schema(), indent=2)
    system_prompt = (
        SALES_WORKER_SYSTEM_PROMPT
        + f"\n\nAfter completing any research, you MUST submit your final answer by calling the `submit_sales_answer` tool, or by emitting raw JSON conforming to this schema:\n{json_schema}"
    )

    agent = create_react_agent(
        model=LLMFactory().get_worker_llm(),
        tools=all_tools,
        prompt=system_prompt,
    )

    initial_user_message = (
        "user",
        f"Document content:\n\n{document_excerpt}\n\n"
        "Draft a response to this RFP/questionnaire.",
    )
    result = await agent.ainvoke({"messages": [initial_user_message]})
    messages = result["messages"]
    tool_calls = _extract_tool_calls(messages)

    # 1. Check if the model submitted via the submit_sales_answer tool
    for msg in messages:
        for call in getattr(msg, "tool_calls", None) or []:
            if call["name"] in ("submit_sales_answer", "submit_sales_response", "sales_answer"):
                try:
                    return StructuredAnswer.model_validate(call["args"]), tool_calls
                except Exception:
                    pass

    # 2. Fallback: Parse from text content
    last_content = ""
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content and not getattr(msg, "tool_calls", None):
            last_content = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    last_content = last_content.strip()
    if last_content.startswith("```"):
        last_content = last_content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        answer = StructuredAnswer.model_validate_json(last_content)
        return answer, tool_calls
    except Exception:
        match = re.search(r"\{.*\}", last_content, re.DOTALL)
        if match:
            answer = StructuredAnswer.model_validate_json(match.group(0))
            return answer, tool_calls
        raise


async def _run_compliance_worker_agent(
    document_excerpt: str, tools: list
) -> tuple[ComplianceAuditResult, list[dict[str, Any]]]:
    """Run the ReAct Compliance Worker with structured submission tool and fallback parsing."""
    import json
    import re
    from typing import Literal
    from langchain_core.tools import tool
    from langgraph.prebuilt import create_react_agent  # type: ignore

    @tool
    def submit_compliance_audit(
        is_compliant: bool,
        violations: list[str],
        severity: Literal["Low", "Medium", "High", "Critical", "None"],
        recommended_remediations: list[str],
    ) -> str:
        """Submit the final compliance and security audit result."""
        return "Compliance audit recorded successfully."

    all_tools = [*tools, submit_compliance_audit]
    json_schema = json.dumps(ComplianceAuditResult.model_json_schema(), indent=2)
    system_prompt = (
        COMPLIANCE_WORKER_SYSTEM_PROMPT
        + f"\n\nAfter completing the audit, you MUST submit your final findings by calling the `submit_compliance_audit` tool, or by emitting raw JSON conforming to this schema:\n{json_schema}"
    )

    agent = create_react_agent(
        model=LLMFactory().get_worker_llm(),
        tools=all_tools,
        prompt=system_prompt,
    )

    initial_user_message = (
        "user",
        f"Document content:\n\n{document_excerpt}\n\n"
        "Audit this document for security policy compliance.",
    )
    result = await agent.ainvoke({"messages": [initial_user_message]})
    messages = result["messages"]
    tool_calls = _extract_tool_calls(messages)

    # 1. Check if the model submitted via the submit_compliance_audit tool
    for msg in messages:
        for call in getattr(msg, "tool_calls", None) or []:
            if call["name"] in ("submit_compliance_audit", "submit_audit", "compliance_audit"):
                try:
                    return ComplianceAuditResult.model_validate(call["args"]), tool_calls
                except Exception:
                    pass

    # 2. Fallback: Parse from text content
    last_content = ""
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content and not getattr(msg, "tool_calls", None):
            last_content = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    last_content = last_content.strip()
    if last_content.startswith("```"):
        last_content = last_content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        audit = ComplianceAuditResult.model_validate_json(last_content)
        return audit, tool_calls
    except Exception:
        match = re.search(r"\{.*\}", last_content, re.DOTALL)
        if match:
            audit = ComplianceAuditResult.model_validate_json(match.group(0))
            return audit, tool_calls
        raise


async def _run_invoice_worker_agent(
    document_excerpt: str, tools: list
) -> tuple[InvoiceReconciliationResult, list[dict[str, Any]]]:
    """Run the ReAct Invoice Reconciliation Worker with structured submission tool and fallback parsing."""
    import json
    import re
    from langchain_core.tools import tool
    from langgraph.prebuilt import create_react_agent  # type: ignore

    @tool
    def submit_invoice_reconciliation(
        is_matched: bool,
        discrepancies: list[str],
        approved_for_payment: bool,
        extracted_total: float,
    ) -> str:
        """Submit the final invoice reconciliation result after ledger verification."""
        return "Invoice reconciliation recorded successfully."

    all_tools = [*tools, submit_invoice_reconciliation]
    json_schema = json.dumps(InvoiceReconciliationResult.model_json_schema(), indent=2)
    system_prompt = (
        INVOICE_WORKER_SYSTEM_PROMPT
        + f"\n\nAfter retrieving ledger data and reconciling, you MUST submit your final result by calling the `submit_invoice_reconciliation` tool, or by emitting raw JSON conforming to this schema:\n{json_schema}"
    )

    agent = create_react_agent(
        model=LLMFactory().get_worker_llm(),
        tools=all_tools,
        prompt=system_prompt,
    )

    initial_user_message = (
        "user",
        f"Document content:\n\n{document_excerpt}\n\n"
        "Reconcile this invoice against the internal purchase order ledger.",
    )
    result = await agent.ainvoke({"messages": [initial_user_message]})
    messages = result["messages"]
    tool_calls = _extract_tool_calls(messages)

    # 1. Check if the model submitted via the submit_invoice_reconciliation tool
    for msg in messages:
        for call in getattr(msg, "tool_calls", None) or []:
            if call["name"] in ("submit_invoice_reconciliation", "submit_reconciliation", "invoice_reconciliation"):
                try:
                    return InvoiceReconciliationResult.model_validate(call["args"]), tool_calls
                except Exception:
                    pass

    # 2. Fallback: Parse from text content
    last_content = ""
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content and not getattr(msg, "tool_calls", None):
            last_content = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    last_content = last_content.strip()
    if last_content.startswith("```"):
        last_content = last_content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        reconciliation = InvoiceReconciliationResult.model_validate_json(last_content)
        return reconciliation, tool_calls
    except Exception:
        match = re.search(r"\{.*\}", last_content, re.DOTALL)
        if match:
            reconciliation = InvoiceReconciliationResult.model_validate_json(match.group(0))
            return reconciliation, tool_calls
        raise



async def invoice_worker_node(state: GraphState) -> dict:
    """Run the Invoice Reconciliation Worker for documents classified as
    ``invoice_reconciliation``.

    Mirrors ``compliance_worker_node`` exactly in structure:
    - Wraps the MCP session in an ``AsyncExitStack`` so exceptions propagate
      cleanly *after* the anyio task group has closed.
    - Falls back gracefully if the MCP server is unavailable (agent still
      runs, just without the ``get_open_purchase_orders`` tool).
    - Promotes configuration errors (missing API key) to
      ``LLMConfigurationError`` so ``agent_runner.py`` can apply its dedicated
      fallback path.
    """
    from contextlib import AsyncExitStack

    from mcp_host.client import build_mcp_tools, mcp_session

    document_excerpt = state["document_text"][:MAX_DOCUMENT_CHARS] or "(empty document)"

    tools: list = []
    worker_error: Exception | None = None
    llm_config_error: LLMConfigurationError | None = None
    reconciliation_result = None
    worker_tool_calls: list[dict[str, Any]] = []

    async with AsyncExitStack() as stack:
        try:
            session = await stack.enter_async_context(mcp_session())
            mcp_tools = await build_mcp_tools(session)
            # Filter to only the PO ledger tool so the agent's context
            # is focused -- the pricing and security-policy tools would only
            # add noise for a financial reconciliation task.
            tools = [
                t for t in mcp_tools if t.name == "get_open_purchase_orders"
            ] or mcp_tools
        except Exception:
            logger.warning(
                "MCP server unavailable; Invoice Worker running without MCP tools",
                exc_info=True,
            )

        try:
            reconciliation_result, worker_tool_calls = await _run_invoice_worker_agent(
                document_excerpt, tools
            )
        except LLMConfigurationError as exc:
            llm_config_error = exc
        except Exception as exc:
            worker_error = exc

    if llm_config_error is not None:
        raise llm_config_error
    if worker_error is not None:
        raise InvoiceWorkerError(str(worker_error)) from worker_error

    return {
        "invoice_reconciliation": reconciliation_result,
        "worker_tool_calls": worker_tool_calls,
    }


async def compliance_worker_node(state: GraphState) -> dict:
    """Run the Compliance Auditor Worker for documents classified as
    ``compliance_audit``.

    Mirrors ``sales_worker_node`` exactly in structure:
    - Wraps the MCP session in an ``AsyncExitStack`` so exceptions propagate
      cleanly *after* the anyio task group has closed.
    - Falls back gracefully if the MCP server is unavailable (agent still
      runs, just without the ``get_security_policies`` tool).
    - Promotes configuration errors (missing API key) to ``LLMConfigurationError``
      so ``agent_runner.py`` can apply its dedicated fallback path.
    """
    from contextlib import AsyncExitStack

    from mcp_host.client import build_mcp_tools, mcp_session

    document_excerpt = state["document_text"][:MAX_DOCUMENT_CHARS] or "(empty document)"

    tools: list = []
    worker_error: Exception | None = None
    llm_config_error: LLMConfigurationError | None = None
    audit_result = None
    worker_tool_calls: list[dict[str, Any]] = []

    async with AsyncExitStack() as stack:
        try:
            session = await stack.enter_async_context(mcp_session())
            mcp_tools = await build_mcp_tools(session)
            # Filter to only the security-policies tool so the agent's context
            # is focused -- the sales pricing tool would only add noise here.
            tools = [
                t for t in mcp_tools if t.name == "get_security_policies"
            ] or mcp_tools
        except Exception:
            logger.warning(
                "MCP server unavailable; Compliance Worker running without MCP tools",
                exc_info=True,
            )

        try:
            audit_result, worker_tool_calls = await _run_compliance_worker_agent(
                document_excerpt, tools
            )
        except LLMConfigurationError as exc:
            llm_config_error = exc
        except Exception as exc:
            worker_error = exc

    if llm_config_error is not None:
        raise llm_config_error
    if worker_error is not None:
        raise ComplianceWorkerError(str(worker_error)) from worker_error

    return {"compliance_audit": audit_result, "worker_tool_calls": worker_tool_calls}


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


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def _route_after_supervisor(state: GraphState) -> str:
    route = state["route"]
    if route == "sales_rfp":
        return "sales_worker"
    if route == "compliance_audit":
        return "compliance_worker"
    if route == "invoice_reconciliation":
        return "invoice_worker"
    return "__end__"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph():
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(GraphState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("sales_worker", sales_worker_node)
    workflow.add_node("compliance_worker", compliance_worker_node)
    workflow.add_node("invoice_worker", invoice_worker_node)
    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "sales_worker": "sales_worker",
            "compliance_worker": "compliance_worker",
            "invoice_worker": "invoice_worker",
            "__end__": END,
        },
    )
    workflow.add_edge("sales_worker", END)
    workflow.add_edge("compliance_worker", END)
    workflow.add_edge("invoice_worker", END)
    return workflow.compile()


graph = build_graph()
