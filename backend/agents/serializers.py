# pyright: reportIncompatibleVariableOverride=false, reportIncompatibleMethodOverride=false
from rest_framework import serializers

from .models import AgentProfile, AgentRun, Answer, ToolCall


class AgentProfileSerializer(serializers.ModelSerializer):
    class Meta:  # type: ignore
        model = AgentProfile
        fields = [
            "id",
            "name",
            "system_prompt",
            "model_name",
            "temperature",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:  # type: ignore
        model = Answer
        fields = [
            "id",
            "agent_run",
            "question_text",
            "content",
            "executive_summary",
            "risk_flags",
            "action_items",
            "confidence_score",
            "is_verified",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = fields


class ToolCallSerializer(serializers.ModelSerializer):
    tool_input = serializers.JSONField(source="input_data", read_only=True)
    tool_output = serializers.JSONField(source="output_data", read_only=True)

    class Meta:  # type: ignore
        model = ToolCall
        fields = [
            "id",
            "agent_run",
            "tool_name",
            "tool_input",
            "tool_output",
            "created_at",
        ]
        read_only_fields = fields


class AgentRunSerializer(serializers.ModelSerializer):
    agent_profile_name = serializers.CharField(
        source="agent_profile.name", read_only=True
    )
    document_name = serializers.CharField(source="document.file_path", read_only=True)
    tool_calls_count = serializers.IntegerField(
        source="tool_calls.count", read_only=True
    )

    class Meta:  # type: ignore
        model = AgentRun
        fields = [
            "id",
            "document",
            "document_name",
            "agent_profile",
            "agent_profile_name",
            "status",
            "started_at",
            "finished_at",
            "error_message",
            "tool_calls_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
