"""Centralized registry for agent tools, plus the concrete tools themselves.

`ToolRegistry` is the generic name -> tool lookup for future static/global
LangChain/MCP tools, collected once and handed to LangGraph agents. The
concrete `search_company_knowledge` tool below is *not* registered there
because it's organization-scoped: `build_search_company_knowledge_tool()` is a
factory that binds a specific `organization_id` at graph-build time (once per
document run), since the LLM shouldn't need to know/guess the org's UUID.
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


def build_search_company_knowledge_tool(organization_id: str):
    """Build a `search_company_knowledge` tool bound to one organization.

    Wraps `memory.vector_client.ChromaDBClient.semantic_search` so a Worker
    agent can retrieve relevant prior documents/answers for this organization
    without ever seeing or supplying the organization's UUID itself.
    """
    from langchain_core.tools import tool

    from memory.vector_client import ChromaDBClient

    @tool
    def search_company_knowledge(query: str) -> str:
        """Search this organization's prior documents and answers for context
        relevant to the given query. Use this to find similar past RFP
        answers, policies, or facts before drafting a new response."""
        client = ChromaDBClient(collection_name=f"org_{organization_id}")
        results = client.semantic_search(query, top_k=5)

        if not results:
            return "No relevant prior context found."

        return "\n\n".join(
            f"[{r['metadata'].get('file_name', 'unknown')}] {r['text']}"
            for r in results
        )

    return search_company_knowledge
