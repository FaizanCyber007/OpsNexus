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

from typing import Literal, TypedDict

from pydantic import BaseModel, Field

from orchestration.model_client import LLMFactory
from orchestration.tool_registry import build_search_company_knowledge_tool

ROUTES = Literal[
    "sales_rfp", "invoice_reconciliation", "compliance_audit", "general_intake"
]

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
accordingly."""


class ClassificationResult(BaseModel):
    route: ROUTES
    reasoning: str = Field(
        description="One or two sentences explaining the classification"
    )


class StructuredAnswer(BaseModel):
    content: str = Field(description="The synthesized draft response")
    confidence_score: float = Field(ge=0.0, le=1.0)


class GraphState(TypedDict):
    organization_id: str
    document_text: str
    route: str
    reasoning: str
    answer: StructuredAnswer | None


def supervisor_node(state: GraphState) -> dict:
    llm = LLMFactory().get_supervisor_llm().with_structured_output(ClassificationResult)
    document_excerpt = state["document_text"][:MAX_DOCUMENT_CHARS] or "(empty document)"

    result: ClassificationResult = llm.invoke(
        [
            ("system", SUPERVISOR_SYSTEM_PROMPT),
            ("user", f"Document content:\n\n{document_excerpt}"),
        ]
    )
    return {"route": result.route, "reasoning": result.reasoning}


def sales_worker_node(state: GraphState) -> dict:
    from langgraph.prebuilt import create_react_agent

    tool = build_search_company_knowledge_tool(state["organization_id"])
    agent = create_react_agent(
        model=LLMFactory().get_worker_llm(),
        tools=[tool],
        prompt=SALES_WORKER_SYSTEM_PROMPT,
        response_format=StructuredAnswer,
    )

    document_excerpt = state["document_text"][:MAX_DOCUMENT_CHARS] or "(empty document)"
    result = agent.invoke(
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

    return {"answer": result["structured_response"]}


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
