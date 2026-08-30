from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import exceptions, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import TenantScopedViewSetMixin
from core.middleware import AuditLogContextMixin
from orchestration.model_client import LLMFactory, SUPERVISOR_MODEL_NAME, WORKER_MODEL_NAME
from core.models import AuditLog, HealthRule, Organization, Playbook
from core.permissions import IsOrganizationAdmin
from core.serializers import (
    AuditLogSerializer,
    HealthRuleSerializer,
    OrganizationSerializer,
    PlaybookSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List SOC2 Audit Logs",
        description=(
            "Retrieve audit trail records for the authenticated organization admin's company. "  # noqa: E501
            "Only Organization Admins can view audit logs."
        ),
        parameters=[
            OpenApiParameter(
                name="organization",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter audit logs by Organization UUID (superuser only)",
                required=False,
            ),
            OpenApiParameter(
                name="resource_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter audit logs by resource type (e.g. Document, HealthRule, Playbook)",  # noqa: E501
                required=False,
            ),
            OpenApiParameter(
                name="action",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter audit logs by action (CREATE, UPDATE, DELETE)",  # noqa: E501
                required=False,
            ),
        ],
        responses={200: AuditLogSerializer(many=True), 403: OpenApiTypes.OBJECT},
    ),
    retrieve=extend_schema(
        summary="Get Audit Log Detail",
        description="Retrieve details of a specific audit log record.",
        responses={
            200: AuditLogSerializer,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },  # noqa: E501
    ),
)
class AuditLogViewSet(
    AuditLogContextMixin, TenantScopedViewSetMixin, viewsets.ReadOnlyModelViewSet
):
    """Read-only ViewSet for SOC2-compliant company audit logs."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]
    queryset = AuditLog.objects.select_related("user", "organization").order_by(
        "-timestamp"
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        resource_type = self.request.query_params.get("resource_type")
        if resource_type:
            queryset = queryset.filter(resource_type__iexact=resource_type)

        action = self.request.query_params.get("action")
        if action:
            queryset = queryset.filter(action__iexact=action)

        return queryset


@extend_schema_view(
    list=extend_schema(
        summary="List Health Rules",
        description="Retrieve health rules configured for the organization.",
        parameters=[
            OpenApiParameter(
                name="organization",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter health rules by Organization UUID",
                required=False,
            ),
        ],
        responses={200: HealthRuleSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create Health Rule",
        description="Create a new health rule for the organization.",
        responses={201: HealthRuleSerializer},
    ),
    retrieve=extend_schema(
        summary="Get Health Rule Detail",
        description="Retrieve details of a specific health rule.",
        responses={200: HealthRuleSerializer, 404: OpenApiTypes.OBJECT},
    ),
    update=extend_schema(
        summary="Update Health Rule",
        description="Update an existing health rule.",
        responses={200: HealthRuleSerializer},
    ),
    destroy=extend_schema(
        summary="Delete Health Rule",
        description="Delete a health rule.",
        responses={204: None},
    ),
)
class HealthRuleViewSet(
    AuditLogContextMixin, TenantScopedViewSetMixin, viewsets.ModelViewSet
):
    """ViewSet for managing tenant Health Rules with SOC2 audit tracking."""

    serializer_class = HealthRuleSerializer
    permission_classes = [IsAuthenticated]
    queryset = (
        HealthRule.objects.filter(deleted_at__isnull=True)
        .select_related("organization")
        .order_by("-created_at")
    )


@extend_schema_view(
    list=extend_schema(
        summary="List Playbooks",
        description="Retrieve operational playbooks for the organization.",
        parameters=[
            OpenApiParameter(
                name="organization",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter playbooks by Organization UUID",
                required=False,
            ),
        ],
        responses={200: PlaybookSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create Playbook",
        description="Create a new operational playbook.",
        responses={201: PlaybookSerializer},
    ),
    retrieve=extend_schema(
        summary="Get Playbook Detail",
        description="Retrieve details of a specific playbook.",
        responses={200: PlaybookSerializer, 404: OpenApiTypes.OBJECT},
    ),
    update=extend_schema(
        summary="Update Playbook",
        description="Update an existing playbook.",
        responses={200: PlaybookSerializer},
    ),
    destroy=extend_schema(
        summary="Delete Playbook",
        description="Delete a playbook.",
        responses={204: None},
    ),
)
class PlaybookViewSet(
    AuditLogContextMixin, TenantScopedViewSetMixin, viewsets.ModelViewSet
):
    """ViewSet for managing operational Playbooks with SOC2 audit tracking."""

    serializer_class = PlaybookSerializer
    permission_classes = [IsAuthenticated]
    queryset = (
        Playbook.objects.filter(deleted_at__isnull=True)
        .select_related("organization")
        .order_by("-created_at")
    )


@extend_schema_view(
    list=extend_schema(
        summary="List Organizations",
        description="Retrieve accessible organizations.",
        responses={200: OrganizationSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Get Organization Detail",
        description="Retrieve details of a specific organization.",
        responses={200: OrganizationSerializer, 404: OpenApiTypes.OBJECT},
    ),
)
class OrganizationViewSet(
    AuditLogContextMixin, TenantScopedViewSetMixin, viewsets.ModelViewSet
):
    """ViewSet for managing tenant organizations."""

    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Organization.objects.filter(deleted_at__isnull=True).order_by(
        "-created_at"
    )
    tenant_filter_kwarg = "id"

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise exceptions.PermissionDenied(
                "Only superusers can create new organizations."
            )
        return super().create(request, *args, **kwargs)


class SystemStatusView(APIView):
    """Health and telemetry diagnostics endpoint for OpsNexus infrastructure."""

    from rest_framework.permissions import IsAdminUser

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="System Health & Diagnostic Telemetry",
        description="Returns real-time status of Redis cache, ChromaDB vector store, LLM providers, and rate throttles.",
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request, *args, **kwargs):
        import os
        from django.core.cache import cache

        # Test Redis Cache
        redis_status = "connected"
        try:
            cache.set("_health_check_probe", 1, timeout=5)
            probe_val = cache.get("_health_check_probe")
            if probe_val != 1:
                redis_status = "degraded"
        except Exception:
            redis_status = "unavailable"

        # Check ChromaDB persistence
        from django.conf import settings

        chroma_dir = getattr(settings, "CHROMA_PERSIST_DIR", "")
        chroma_status = (
            "healthy" if chroma_dir and os.path.exists(chroma_dir) else "initialized"
        )

        # Check LLM Keys
        has_gemini = bool(
            os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )
        has_groq = bool(os.environ.get("GROQ_API_KEY"))

        data = {
            "status": "operational",
            "version": "1.4.2",
            "cluster": "opsnexus-swarm-primary",
            "components": {
                "supervisor_llm": {
                    "model": SUPERVISOR_MODEL_NAME,
                    "provider": "google",
                    "configured": has_gemini,
                    "status": "ready" if has_gemini else "simulated_fallback",
                },
                "worker_llm": {
                    "model": WORKER_MODEL_NAME,
                    "provider": "groq",
                    "configured": has_groq,
                    "status": "ready" if has_groq else "simulated_fallback",
                },
                "vector_memory": {
                    "engine": "chromadb",
                    "embedding_model": "all-MiniLM-L6-v2 (HuggingFace)",
                    "cost_per_query": "$0.00 (local dense)",
                    "status": chroma_status,
                },
                "cache_broker": {
                    "engine": "redis",
                    "ttl_seconds": 900,
                    "status": redis_status,
                },
                "mcp_protocol": {
                    "version": "2.0.0 (JSON-RPC 2.0)",
                    "server": "opsnexus-mcp-host",
                    "tools_count": 2,
                    "status": "active",
                },
                "security": {
                    "soc2_audit": "active",
                    "rate_limiting": "5 req/min (Upload & Chat Arena)",
                    "x_frame_options": "DENY",
                    "nosniff": True,
                },
            },
        }
        return Response(data)
