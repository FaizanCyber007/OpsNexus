from rest_framework import serializers

from .models import Answer, ToolCall


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
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
    tool_input = serializers.JSONField(source="input_data")
    tool_output = serializers.JSONField(source="output_data")

    class Meta:
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
