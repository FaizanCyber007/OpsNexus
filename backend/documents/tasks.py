"""RQ-backed asynchronous task queue for document ingestion & agent execution."""

import asyncio
import logging
import uuid

from django.db import connection
from django_rq import job

from documents.models import Document
from memory.vector_client import ingest_document
from orchestration.agent_runner import trigger_agent_run

logger = logging.getLogger(__name__)


@job("default")
def process_document_task(document_id: str | uuid.UUID) -> None:
    """Execute vector ingestion and LangGraph agent execution for a document."""
    try:
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            logger.exception(
                "Document %s not found for background processing", document_id
            )
            return

        try:
            ingest_document(document)
        except Exception:
            logger.exception("Memory ingestion failed for document %s", document_id)

        try:
            asyncio.run(trigger_agent_run(document_id))
        except Exception:
            logger.exception("Agent run failed for document %s", document_id)
            try:
                document = Document.objects.get(id=document_id)
            except Document.DoesNotExist:
                logger.exception(
                    "Document %s vanished while marking agent run failed",
                    document_id,
                )
                return
            document.status = Document.Status.FAILED
            document.save(update_fields=["status"])
    finally:
        connection.close()


def enqueue_document_processing(document_id: str | uuid.UUID) -> bool:
    """Enqueue document processing task into RQ queue."""
    try:
        process_document_task.delay(document_id)
        logger.info("Enqueued document processing task to RQ queue: %s", document_id)
        return True
    except Exception:
        logger.exception(
            "Failed to enqueue document processing task to RQ queue: %s",
            document_id,
        )
        return False
