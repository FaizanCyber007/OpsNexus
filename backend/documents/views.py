import asyncio
import logging
import threading

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from agents.models import Answer
from agents.serializers import AnswerSerializer
from memory.vector_client import ingest_document
from orchestration.agent_runner import trigger_agent_run

from .models import Document
from .serializers import DocumentSerializer

logger = logging.getLogger(__name__)


def _run_mock_agent_in_background(document_id) -> None:
    document = Document.objects.get(id=document_id)

    try:
        ingest_document(document)
    except Exception:
        logger.exception("Memory ingestion failed for document %s", document_id)

    try:
        asyncio.run(trigger_agent_run(document_id))
    except Exception:
        logger.exception("Agent run failed for document %s", document_id)
        document.status = Document.Status.FAILED
        document.save(update_fields=["status"])


class DocumentViewSet(ModelViewSet):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        queryset = Document.objects.filter(deleted_at__isnull=True).order_by(
            "-created_at"
        )
        organization_id = self.request.query_params.get("organization")
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        return queryset

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        document.deleted_at = timezone.now()
        document.save(update_fields=["deleted_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        if document.file and not document.file_path:
            document.file_path = document.file.name
            document.save(update_fields=["file_path"])

        threading.Thread(
            target=_run_mock_agent_in_background,
            args=(document.id,),
            daemon=True,
        ).start()

        return Response(
            {"status": "processing", "document_id": document.id},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"])
    def answers(self, request, pk=None):
        answers = Answer.objects.filter(agent_run__document_id=pk).order_by(
            "created_at"
        )
        return Response(AnswerSerializer(answers, many=True).data)
