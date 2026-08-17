"""Keep the ChromaDB memory layer in sync when a Document is deleted.

Without this, `search_company_knowledge` (orchestration/tool_registry.py) can
keep retrieving and citing a document's vectors after the document itself has
been deleted or soft-deleted -- "ghost data" in agent answers.
"""

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from memory.vector_client import ChromaDBClient, get_organization_collection_name

from .models import Document

logger = logging.getLogger(__name__)


def _delete_document_vectors(document: Document) -> None:
    try:
        client = ChromaDBClient(
            collection_name=get_organization_collection_name(document.organization_id)
        )
        client.delete_by_document_id(str(document.id))
    except Exception:
        logger.exception(
            "Failed to remove ChromaDB vectors for document %s", document.id
        )


@receiver(post_delete, sender=Document)
def cleanup_vectors_on_hard_delete(sender, instance, **kwargs):
    _delete_document_vectors(instance)


@receiver(post_save, sender=Document)
def cleanup_vectors_on_soft_delete(sender, instance, update_fields, **kwargs):
    if (
        update_fields
        and "deleted_at" in update_fields
        and instance.deleted_at is not None
    ):
        _delete_document_vectors(instance)
