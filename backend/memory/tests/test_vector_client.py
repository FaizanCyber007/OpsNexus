import os
import uuid
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from memory.models import PendingVectorCleanup
from memory.vector_client import attempt_pending_cleanup, ingest_document


class _FakeFieldFile:
    """Mimics a Django FieldFile backed by django-storages' S3Storage.

    S3Storage has no local filesystem access, so accessing `.path` raises
    NotImplementedError -- only the storage-agnostic File API (`.open()`/
    `.chunks()`) works. This stub proves ingest_document never touches
    `.path`.
    """

    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content

    @property
    def path(self):
        raise NotImplementedError("This backend doesn't support absolute paths.")

    def open(self, mode="rb"):
        return self

    def chunks(self):
        yield self._content

    def close(self):
        pass

    def __bool__(self):
        return True


class _FakeDocument:
    def __init__(self, file_field, document_id="doc-1", organization_id="org-1"):
        self.file = file_field
        self.id = document_id
        self.organization_id = organization_id


def test_ingest_document_works_without_field_file_path():
    document = _FakeDocument(
        _FakeFieldFile("documents/policy.txt", b"OpsNexus SOC2 policy details.")
    )

    with patch("memory.vector_client.ChromaDBClient") as MockClient:
        ingest_document(document)

    MockClient.return_value.delete_by_document_id.assert_called_once_with("doc-1")
    MockClient.return_value.add_documents.assert_called_once()
    added_docs = MockClient.return_value.add_documents.call_args.args[0]
    assert added_docs[0]["text"].startswith("OpsNexus SOC2 policy")


def test_ingest_document_no_op_for_undecodable_file():
    document = _FakeDocument(_FakeFieldFile("documents/image.png", b"\xff\xd8\xff\xe0"))

    with patch("memory.vector_client.ChromaDBClient") as MockClient:
        ingest_document(document)

    MockClient.return_value.add_documents.assert_not_called()


class _FailingFieldFile(_FakeFieldFile):
    """Raises partway through `.chunks()`, simulating a transient storage
    read failure (e.g. a dropped connection to S3) mid-write."""

    def chunks(self):
        yield self._content[:1]
        raise OSError("simulated storage read failure")


def test_ingest_document_cleans_up_temp_file_on_write_failure():
    document = _FakeDocument(
        _FailingFieldFile("documents/broken.txt", b"partial content")
    )

    with patch("memory.vector_client.ChromaDBClient"), patch(
        "os.remove", wraps=os.remove
    ) as mock_remove:
        with pytest.raises(OSError):
            ingest_document(document)

    mock_remove.assert_called_once()


@pytest.mark.django_db
class TestAttemptPendingCleanup:
    def test_success_deletes_the_pending_record(self):
        pending = PendingVectorCleanup.objects.create(
            document_id=uuid.uuid4(), organization_id=uuid.uuid4()
        )

        with patch("memory.vector_client.ChromaDBClient") as MockClient:
            result = attempt_pending_cleanup(pending)

        assert result is True
        MockClient.return_value.delete_by_document_id.assert_called_once_with(
            str(pending.document_id)
        )
        assert not PendingVectorCleanup.objects.filter(pk=pending.pk).exists()

    def test_failure_keeps_and_updates_the_pending_record(self):
        pending = PendingVectorCleanup.objects.create(
            document_id=uuid.uuid4(), organization_id=uuid.uuid4()
        )

        with patch(
            "memory.vector_client.ChromaDBClient", side_effect=RuntimeError("down")
        ):
            result = attempt_pending_cleanup(pending)

        assert result is False
        pending.refresh_from_db()
        assert pending.attempts == 1
        assert "down" in pending.last_error

    def test_pending_delete_failure_returns_false_without_raising(self):
        """A DB error while deleting the cleanup record after a successful
        ChromaDB deletion must return False without propagating the exception
        so subsequent retry records are still processed.
        """
        pending = PendingVectorCleanup.objects.create(
            document_id=uuid.uuid4(), organization_id=uuid.uuid4()
        )

        with patch("memory.vector_client.ChromaDBClient"), patch.object(
            pending, "delete", side_effect=Exception("db gone")
        ):
            result = attempt_pending_cleanup(pending)

        assert result is False
        # The record was NOT deleted because pending.delete() raised.
        assert PendingVectorCleanup.objects.filter(pk=pending.pk).exists()

    def test_save_failure_during_error_path_returns_false_without_raising(self):
        """A DB error while persisting failure state (attempts/last_error)
        must return False without propagating so subsequent records are processed.
        """
        pending = PendingVectorCleanup.objects.create(
            document_id=uuid.uuid4(), organization_id=uuid.uuid4()
        )

        with patch(
            "memory.vector_client.ChromaDBClient", side_effect=RuntimeError("down")
        ), patch.object(pending, "save", side_effect=Exception("db gone")):
            result = attempt_pending_cleanup(pending)

        assert result is False


@pytest.mark.django_db
class TestRetryVectorCleanupCommand:
    def test_retries_and_resolves_successful_records(self):
        pending = PendingVectorCleanup.objects.create(
            document_id=uuid.uuid4(), organization_id=uuid.uuid4()
        )
        out = StringIO()

        with patch("memory.vector_client.ChromaDBClient"):
            call_command("retry_vector_cleanup", stdout=out)

        assert not PendingVectorCleanup.objects.filter(pk=pending.pk).exists()
        assert "1 succeeded" in out.getvalue()

    def test_keeps_records_that_still_fail(self):
        pending = PendingVectorCleanup.objects.create(
            document_id=uuid.uuid4(), organization_id=uuid.uuid4()
        )
        out = StringIO()

        with patch(
            "memory.vector_client.ChromaDBClient", side_effect=RuntimeError("down")
        ):
            call_command("retry_vector_cleanup", stdout=out)

        pending.refresh_from_db()
        assert pending.attempts == 1
        assert "still pending" in out.getvalue()
