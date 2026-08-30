# pyright: reportIncompatibleVariableOverride=false, reportIncompatibleMethodOverride=false
"""DRF Serializers for core app models (AuditLog, HealthRule, Playbook, Organization, UserProfile)."""

from rest_framework import serializers

from core.models import AuditLog, HealthRule, Organization, Playbook, UserProfile


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for SOC2 Audit Log records."""

    user_id = serializers.UUIDField(source="user.id", read_only=True, allow_null=True)
    username = serializers.CharField(
        source="user.username", read_only=True, allow_null=True
    )
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)

    class Meta:  # type: ignore
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

    class Meta:  # type: ignore
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

    class Meta:  # type: ignore
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


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization instances."""

    class Meta:  # type: ignore
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile instances."""

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)

    class Meta:  # type: ignore
        model = UserProfile
        fields = [
            "id",
            "user",
            "username",
            "email",
            "organization",
            "role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
