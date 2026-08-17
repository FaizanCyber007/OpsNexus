from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    latest_agent_run_id = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "organization",
            "doc_type",
            "status",
            "file",
            "file_path",
            "latest_agent_run_id",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "file_path",
            "latest_agent_run_id",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def get_latest_agent_run_id(self, obj):
        agent_run = obj.agent_runs.order_by("-created_at").first()
        return str(agent_run.id) if agent_run else None
