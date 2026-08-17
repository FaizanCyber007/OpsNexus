from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import AgentRun
from .serializers import ToolCallSerializer


class AgentRunViewSet(GenericViewSet):
    queryset = AgentRun.objects.filter(deleted_at__isnull=True)

    @action(detail=True, methods=["get"], url_path="tool-calls")
    def tool_calls(self, request, pk=None):
        agent_run = self.get_object()
        calls = agent_run.tool_calls.order_by("created_at")
        return Response(ToolCallSerializer(calls, many=True).data)
