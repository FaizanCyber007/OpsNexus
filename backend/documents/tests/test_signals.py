from unittest.mock import patch

import pytest
from django.utils import timezone

from documents.factories import DocumentFactory
from memory.vector_client import get_organization_collection_name


def _immediate_commit():
    """Patch transaction.on_commit so its callback runs synchronously.

    pytest.mark.django_db wraps each test in a transaction that's rolled back
    at the end, so on_commit callbacks never fire otherwise -- same pattern
    already used in documents/tests/test_views.py for the upload endpoint's
    on_commit-wrapped thread start.
    """
    return patch("django.db.transaction.on_commit", side_effect=lambda cb: cb())


@pytest.mark.django_db
class TestDocumentVectorCleanupSignals:
    def test_hard_delete_triggers_chroma_cleanup(self):
        document = DocumentFactory()
        document_id = document.id
        organization_id = document.organization_id

        with _immediate_commit(), patch(
            "documents.signals.ChromaDBClient"
        ) as MockClient:
            document.delete()

        MockClient.assert_called_once_with(
            collection_name=get_organization_collection_name(organization_id)
        )
        MockClient.return_value.delete_by_document_id.assert_called_once_with(
            str(document_id)
        )

    def test_soft_delete_triggers_chroma_cleanup(self):
        document = DocumentFactory()

        with _immediate_commit(), patch(
            "documents.signals.ChromaDBClient"
        ) as MockClient:
            document.deleted_at = timezone.now()
            document.save(update_fields=["deleted_at"])

        MockClient.assert_called_once_with(
            collection_name=get_organization_collection_name(document.organization_id)
        )
        MockClient.return_value.delete_by_document_id.assert_called_once_with(
            str(document.id)
        )

    def test_soft_delete_via_plain_save_triggers_chroma_cleanup(self):
        """A caller that just calls .save() (no update_fields) must still
        trigger cleanup -- detection relies on the actual deleted_at
        transition (pre_save vs post_save), not on the update_fields kwarg."""
        document = DocumentFactory()

        with _immediate_commit(), patch(
            "documents.signals.ChromaDBClient"
        ) as MockClient:
            document.deleted_at = timezone.now()
            document.save()

        MockClient.assert_called_once_with(
            collection_name=get_organization_collection_name(document.organization_id)
        )
        MockClient.return_value.delete_by_document_id.assert_called_once_with(
            str(document.id)
        )

    def test_unrelated_save_does_not_trigger_cleanup(self):
        document = DocumentFactory()

        with _immediate_commit(), patch(
            "documents.signals.ChromaDBClient"
        ) as MockClient:
            document.status = document.Status.COMPLETED
            document.save(update_fields=["status"])

        MockClient.assert_not_called()

    def test_chroma_failure_does_not_raise(self):
        document = DocumentFactory()

        with _immediate_commit(), patch(
            "documents.signals.ChromaDBClient", side_effect=RuntimeError("down")
        ):
            # Should not raise -- a Chroma outage must not fail the delete.
            document.delete()
