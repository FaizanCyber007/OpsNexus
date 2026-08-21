"""Redis-backed asynchronous task queue for document ingestion & agent execution."""

import asyncio
import json
import logging
import uuid
from typing import Any

from django.db import connection
from django.utils import timezone
from django_redis import get_redis_connection

from documents.models import Document
from memory.vector_client import ingest_document
from orchestration.agent_runner import trigger_agent_run

logger = logging.getLogger(__name__)

REDIS_DOCUMENT_QUEUE_KEY = "opsnexus:tasks:document_processing"


def process_document_task(document_id: Any) -> None:
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
    """Enqueue document processing task into Redis queue."""
    doc_id_str = str(document_id)
    payload = json.dumps(
        {
            "document_id": doc_id_str,
            "enqueued_at": timezone.now().isoformat(),
        }
    )

    try:
        redis_client = get_redis_connection("default")
        redis_client.rpush(REDIS_DOCUMENT_QUEUE_KEY, payload)
        logger.info("Enqueued document processing task to Redis queue: %s", doc_id_str)
        return True
    except Exception:
        logger.exception(
            "Failed to enqueue document processing task to Redis queue: %s",
            doc_id_str,
        )
        return False


def process_next_document_task(timeout: int = 1) -> bool:
    """Consume and execute a single document processing task from the Redis queue."""
    try:
        redis_client = get_redis_connection("default")
        item = redis_client.blpop(REDIS_DOCUMENT_QUEUE_KEY, timeout=timeout)
        if not item:
            return False
        _, payload_bytes = item
        data = json.loads(payload_bytes)
        document_id = data.get("document_id")
        if document_id:
            process_document_task(document_id)
        return True
    except Exception:
        logger.exception("Error consuming document processing task from Redis queue")
        return False
