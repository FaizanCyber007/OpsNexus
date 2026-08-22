import json
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.middleware import AuditLogContextMixin
from .models import AgentProfile, AgentRun
from .serializers import AgentProfileSerializer, AgentRunSerializer, ToolCallSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List Agent Profiles",
        description="Retrieve all configured AI agent profiles and model parameters.",
        responses={200: AgentProfileSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Get Agent Profile Detail",
        description="Retrieve details of a specific agent profile.",
        responses={200: AgentProfileSerializer, 404: OpenApiTypes.OBJECT},
    ),
)
class AgentProfileViewSet(AuditLogContextMixin, viewsets.ReadOnlyModelViewSet):
    """ReadOnly ViewSet for configured agent profiles and model prompts."""

    queryset = AgentProfile.objects.filter(deleted_at__isnull=True).order_by("-created_at")
    serializer_class = AgentProfileSerializer
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    list=extend_schema(
        summary="List Agent Runs",
        description="Retrieve history of all autonomous agent execution runs.",
        parameters=[
            OpenApiParameter(
                name="document",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter runs by Document UUID",
                required=False,
            ),
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter runs by execution status (pending, running, succeeded, failed)",
                required=False,
            ),
        ],
        responses={200: AgentRunSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Get Agent Run Detail",
        description="Retrieve details of a specific agent execution run.",
        responses={200: AgentRunSerializer, 404: OpenApiTypes.OBJECT},
    ),
    tool_calls=extend_schema(
        summary="List Agent Run Tool Calls",
        description=(
            "Retrieve the chronological execution trace of all tools called "
            "during a specific agent run, including MCP tools, classification, "
            "and knowledge searches."
        ),
        responses={
            200: ToolCallSerializer(many=True),
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Tool Call Trace Example",
                response_only=True,
                status_codes=["200"],
                value=[
                    {
                        "id": "1e2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
                        "agent_run": "8f8b89d4-1a35-43ea-ba8d-a411a7b45388",
                        "tool_name": "langgraph_supervisor_classify",
                        "tool_input": {
                            "document_id": "8f8b89d4-1a35-43ea-ba8d-a411a7b45388"
                        },
                        "tool_output": {
                            "route": "sales_rfp",
                            "reasoning": "RFP security questionnaire.",
                        },
                        "created_at": "2026-08-21T00:00:00Z",
                    }
                ],
            )
        ],
    ),
)
class AgentRunViewSet(AuditLogContextMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for inspecting agent execution runs and tool traces."""

    queryset = AgentRun.objects.filter(deleted_at__isnull=True).select_related(
        "document", "agent_profile"
    ).order_by("-created_at")
    serializer_class = AgentRunSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(document__organization=self.request.user.profile.organization)
        document_id = self.request.query_params.get("document")
        if document_id:
            queryset = queryset.filter(document_id=document_id)

        run_status = self.request.query_params.get("status")
        if run_status:
            queryset = queryset.filter(status=run_status)

        return queryset

    @action(detail=True, methods=["get"], url_path="tool-calls")
    def tool_calls(self, request, pk=None):
        agent_run = self.get_object()
        calls = agent_run.tool_calls.select_related("agent_run").order_by("created_at")
        return Response(ToolCallSerializer(calls, many=True).data)


class MCPToolsView(APIView):
    """API endpoint for listing MCP 2.0 tools and executing test runs."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Registered MCP Tools",
        description="Retrieve catalog of registered Model Context Protocol (MCP 2.0) tools and JSON-RPC schemas.",
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request, *args, **kwargs):
        tools = [
            {
                "name": "get_internal_pricing_policy",
                "description": "Return OpsNexus internal tier pricing policy as JSON for RFP/questionnaire resolution.",
                "server": "opsnexus-mcp-host (JSON-RPC stdio)",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
                "transport": "stdio / JSON-RPC 2.0",
                "status": "online",
            },
            {
                "name": "search_company_knowledge",
                "description": "Semantic search over per-tenant vector collection in ChromaDB.",
                "server": "memory.vector_client.ChromaDBClient",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Semantic search query string",
                        }
                    },
                    "required": ["query"],
                },
                "transport": "in-process / LangChain Tool",
                "status": "online",
            },
        ]
        return Response({"tools": tools, "server_version": "2.0.0"})

    @extend_schema(
        summary="Execute MCP Tool Test",
        description="Execute a test invocation of an MCP tool and receive live JSON output.",
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request, *args, **kwargs):
        tool_name = request.data.get("tool_name")
        params = request.data.get("params", {})

        if tool_name == "get_internal_pricing_policy":
            from mcp_host.server import get_internal_pricing_policy

            raw = get_internal_pricing_policy()
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = raw
            return Response(
                {
                    "tool": tool_name,
                    "status": "success",
                    "result": parsed,
                }
            )

        if tool_name == "search_company_knowledge":
            query = params.get("query", "security compliance")
            if request.user.is_superuser and "organization_id" in request.data:
                org_id = request.data.get("organization_id")
            else:
                org_id = str(request.user.profile.organization.id)
            from memory.vector_client import ChromaDBClient

            client = ChromaDBClient(collection_name=f"org_{org_id}")
            results = client.semantic_search(query=query, top_k=3)
            return Response(
                {
                    "tool": tool_name,
                    "status": "success",
                    "query": query,
                    "results_count": len(results),
                    "results": results,
                }
            )

        return Response(
            {"error": f"Tool '{tool_name}' not recognized."}, status=400
        )
