import logging

from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from agents.models import AgentRun, Answer
from agents.serializers import AnswerSerializer
from core.middleware import AuditLogContextMixin
from core.mixins import TenantScopedViewSetMixin
from core.throttling import ChatRateThrottle, DocumentUploadRateThrottle
from orchestration.serializers import (
    DocumentChatRequestSerializer,
    DocumentChatResponseSerializer,
    DocumentUploadResponseSerializer,
)

from .models import Document
from .serializers import DocumentSerializer
from .tasks import enqueue_document_processing

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List Documents",
        description=(
            "Retrieve a list of active documents ordered by newest first, "
            "optionally filtered by organization."
        ),
        parameters=[
            OpenApiParameter(
                name="organization",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter documents by Organization UUID",
                required=False,
            ),
        ],
        responses={200: DocumentSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Get Document Details",
        description="Retrieve full details for a specific active document.",
        responses={200: DocumentSerializer, 404: OpenApiTypes.OBJECT},
    ),
    destroy=extend_schema(
        summary="Soft Delete Document",
        description=(
            "Marks a document as soft-deleted (`deleted_at` timestamp set), "
            "excluding it from standard queries."
        ),
        responses={204: None, 404: OpenApiTypes.OBJECT},
    ),
    update=extend_schema(
        summary="Update Document",
        description="Update document details.",
        responses={
            200: DocumentSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    ),
    partial_update=extend_schema(
        summary="Partial Update Document",
        description="Partially update document fields.",
        responses={
            200: DocumentSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    ),
)
class DocumentViewSet(AuditLogContextMixin, TenantScopedViewSetMixin, ModelViewSet):
    """ViewSet for uploading, querying, and managing documents."""

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    tenant_filter_kwarg = "organization"

    def get_throttles(self):
        if getattr(self, "action", None) == "create":
            return [DocumentUploadRateThrottle()]
        if getattr(self, "action", None) == "chat":
            return [ChatRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        latest_agent_run = (
            AgentRun.objects.filter(document=OuterRef("pk"))
            .order_by("-created_at")
            .values("id")[:1]
        )
        queryset = (
            Document.objects.filter(deleted_at__isnull=True)
            .select_related("organization")
            .annotate(latest_agent_run_id_value=Subquery(latest_agent_run))
            .order_by("-created_at")
        )

        # Override self.queryset temporarily so super().get_queryset() works with our annotated base
        self.queryset = queryset
        return super().get_queryset()

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        document.deleted_at = timezone.now()
        document.save(update_fields=["deleted_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Upload Document for Ingestion & Analysis",
        description=(
            "Upload a document (PDF, DOCX, TXT, MD, CSV, LOG). Upon receipt, "
            "triggers asynchronous vector embedding ingestion into ChromaDB and "
            "initiates the LangGraph multi-agent analysis pipeline."
        ),
        request=DocumentSerializer,
        responses={
            202: DocumentUploadResponseSerializer,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Upload Response",
                summary="Asynchronous task accepted",
                response_only=True,
                status_codes=["202"],
                value={
                    "status": "processing",
                    "document_id": "8f8b89d4-1a35-43ea-ba8d-a411a7b45388",
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        if document.file and not document.file_path:
            document.file_path = document.file.name
            document.save(update_fields=["file_path"])

        transaction.on_commit(lambda: enqueue_document_processing(document.id))

        return Response(
            {"status": "processing", "document_id": document.id},
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        summary="Get Extracted Document Answers",
        description=(
            "Retrieve structured answers, summaries, risk flags, "
            "and action items generated for this document."
        ),
        responses={200: AnswerSerializer(many=True), 404: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["get"])
    def answers(self, request, pk=None):
        document = self.get_object()
        answers = (
            Answer.objects.filter(agent_run__document_id=document.id)
            .select_related("agent_run")
            .prefetch_related("citations")
            .order_by("created_at")
        )
        return Response(AnswerSerializer(answers, many=True).data)

    @extend_schema(
        summary="Chat with Document (RAG & Model Arena)",
        description=(
            "Execute RAG query or multi-model comparison against the document "
            "with 15-minute Redis response caching."
        ),
        request=DocumentChatRequestSerializer,
        responses={
            200: DocumentChatResponseSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=True, methods=["post"])
    def chat(self, request, pk=None):
        from orchestration.views import DocumentChatView

        return DocumentChatView.as_view()(request._request, pk=pk)
