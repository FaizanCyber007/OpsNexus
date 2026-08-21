from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.middleware import AuditLogContextMixin
from .models import AgentRun
from .serializers import ToolCallSerializer


@extend_schema_view(
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
class AgentRunViewSet(AuditLogContextMixin, GenericViewSet):
    """ViewSet for inspecting agent execution runs and tool traces."""

    queryset = AgentRun.objects.filter(deleted_at__isnull=True).select_related(
        "document", "agent_profile"
    )

    @action(detail=True, methods=["get"], url_path="tool-calls")
    def tool_calls(self, request, pk=None):
        agent_run = self.get_object()
        calls = agent_run.tool_calls.select_related("agent_run").order_by("created_at")
        return Response(ToolCallSerializer(calls, many=True).data)
