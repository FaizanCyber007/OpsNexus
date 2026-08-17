"""Keep the ChromaDB memory layer in sync when a Document is deleted.

Without this, `search_company_knowledge` (orchestration/tool_registry.py) can
keep retrieving and citing a document's vectors after the document itself has
been deleted or soft-deleted -- "ghost data" in agent answers.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from memory.vector_client import ChromaDBClient, get_organization_collection_name

from .models import Document

logger = logging.getLogger(__name__)


def _delete_document_vectors(document_id, organization_id) -> None:
    try:
        client = ChromaDBClient(
            collection_name=get_organization_collection_name(organization_id)
        )
        client.delete_by_document_id(str(document_id))
    except Exception:
        logger.exception(
            "Failed to remove ChromaDB vectors for document %s", document_id
        )


def _schedule_vector_cleanup(document_id, organization_id) -> None:
    transaction.on_commit(
        lambda: _delete_document_vectors(document_id, organization_id)
    )


@receiver(pre_save, sender=Document)
def capture_previous_deleted_at(sender, instance, **kwargs):
    """Stash the row's pre-save `deleted_at` so post_save can detect a real
    unset -> set transition, independent of whether the caller happened to
    pass `update_fields=["deleted_at"]` -- Django admin, shell one-liners, and
    any future code path that just calls `.save()` must still trigger cleanup.
    """
    if instance.pk is None:
        instance._previous_deleted_at = None
        return
    instance._previous_deleted_at = (
        Document.objects.filter(pk=instance.pk)
        .values_list("deleted_at", flat=True)
        .first()
    )


@receiver(post_delete, sender=Document)
def cleanup_vectors_on_hard_delete(sender, instance, **kwargs):
    _schedule_vector_cleanup(instance.id, instance.organization_id)


@receiver(post_save, sender=Document)
def cleanup_vectors_on_soft_delete(sender, instance, created, **kwargs):
    if created:
        return
    was_deleted = getattr(instance, "_previous_deleted_at", None) is not None
    if not was_deleted and instance.deleted_at is not None:
        _schedule_vector_cleanup(instance.id, instance.organization_id)
