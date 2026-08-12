from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "organization",
            "doc_type",
            "status",
            "file",
            "file_path",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "file_path",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
