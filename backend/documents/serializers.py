# pyright: reportIncompatibleVariableOverride=false, reportIncompatibleMethodOverride=false
import os

from rest_framework import serializers

from .models import Document

# Matches the frontend's MAX_FILE_SIZE_BYTES (frontend/src/lib/fileValidation.ts).
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

# The formats memory.vector_client.extract_text actually documents support for:
# PDFs/Word docs via dedicated loaders, plus the plain-text extensions its own
# docstring names for the UTF-8 fallback path.
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv", ".log"}


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

    def validate_organization(self, value):
        request = self.context.get("request")
        if request and getattr(request, "user", None) and request.user.is_authenticated:
            if not getattr(request.user, "is_superuser", False):
                profile = getattr(request.user, "profile", None)
                if not profile or profile.organization_id != value.id:
                    raise serializers.ValidationError(
                        "You do not have permission to upload documents to "
                        "another organization."
                    )
        return value

    def validate_file(self, value):
        if value.size > MAX_UPLOAD_SIZE_BYTES:
            raise serializers.ValidationError(
                f"File is larger than {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
            )

        extension = os.path.splitext(value.name)[1].lower()
        if extension not in ALLOWED_UPLOAD_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{extension}'. Allowed: "
                f"{', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}."
            )
        return value

    def get_latest_agent_run_id(self, obj):
        annotated = getattr(obj, "latest_agent_run_id_value", None)
        if annotated is not None:
            return str(annotated)

        agent_run = obj.agent_runs.order_by("-created_at").first()
        return str(agent_run.id) if agent_run else None
