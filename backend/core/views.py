import uuid

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import exceptions, viewsets
from rest_framework.permissions import IsAuthenticated

from core.middleware import AuditLogContextMixin
from core.models import AuditLog
from core.permissions import IsOrganizationAdmin
from core.serializers import AuditLogSerializer


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
class AuditLogViewSet(AuditLogContextMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for SOC2-compliant company audit logs."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def get_queryset(self):
        user = self.request.user
        queryset = AuditLog.objects.select_related("user", "organization").order_by(
            "-timestamp"
        )

        if user.is_superuser:
            org_id = self.request.query_params.get("organization")
            if org_id:
                try:
                    uuid.UUID(str(org_id))
                except (ValueError, AttributeError, TypeError):
                    raise exceptions.ValidationError(
                        {"organization": "Invalid UUID format."}
                    )
                queryset = queryset.filter(organization_id=org_id)
        else:
            profile = getattr(user, "profile", None)
            if profile and profile.organization:
                queryset = queryset.filter(organization=profile.organization)
            else:
                queryset = queryset.none()

        resource_type = self.request.query_params.get("resource_type")
        if resource_type:
            queryset = queryset.filter(resource_type__iexact=resource_type)

        action = self.request.query_params.get("action")
        if action:
            queryset = queryset.filter(action__iexact=action)

        return queryset
