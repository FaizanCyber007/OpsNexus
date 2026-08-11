from rest_framework import serializers

from .models import Answer


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = [
            "id",
            "agent_run",
            "question_text",
            "content",
            "confidence_score",
            "is_verified",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = fields
