"""DRF Serializers for core app models (AuditLog, HealthRule, Playbook)."""

from rest_framework import serializers

from core.models import AuditLog, HealthRule, Playbook


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for SOC2 Audit Log records."""

    user_id = serializers.UUIDField(source="user.id", read_only=True, allow_null=True)
    username = serializers.CharField(
        source="user.username", read_only=True, allow_null=True
    )
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user_id",
            "username",
            "organization_id",
            "action",
            "resource_type",
            "resource_id",
            "timestamp",
            "ip_address",
        ]
        read_only_fields = fields


class HealthRuleSerializer(serializers.ModelSerializer):
    """Serializer for HealthRule instances."""

    class Meta:
        model = HealthRule
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "metric",
            "threshold",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PlaybookSerializer(serializers.ModelSerializer):
    """Serializer for Playbook instances."""

    class Meta:
        model = Playbook
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "content",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
