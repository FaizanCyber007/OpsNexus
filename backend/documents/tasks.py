"""RQ-backed asynchronous task queue for document ingestion & agent execution."""

import asyncio
import logging
import uuid

from django.db import connection
from django_rq import job

from documents.models import Document
from memory.vector_client import ingest_document
from orchestration.agent_runner import (
    GRAPH_EXECUTION_TIMEOUT_SECONDS,
    trigger_agent_run,
)

logger = logging.getLogger(__name__)

# Absolute ceiling for the entire task (ingestion + agent run).
# Must be longer than GRAPH_EXECUTION_TIMEOUT_SECONDS to allow the
# graph's own timeout to fire first, but short enough that the RQ
# worker doesn't block forever.
TASK_HARD_TIMEOUT_SECONDS = GRAPH_EXECUTION_TIMEOUT_SECONDS + 60


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
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            loop.run_until_complete(
                asyncio.wait_for(
                    trigger_agent_run(document_id),
                    timeout=TASK_HARD_TIMEOUT_SECONDS,
                )
            )
        except asyncio.TimeoutError:
            logger.error(
                "Task hard timeout (%ds) reached for document %s; "
                "marking as failed.",
                TASK_HARD_TIMEOUT_SECONDS,
                document_id,
            )
            try:
                document = Document.objects.get(id=document_id)
            except Document.DoesNotExist:
                return
            document.status = Document.Status.FAILED
            document.save(update_fields=["status"])
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
