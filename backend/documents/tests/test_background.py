import uuid
from unittest.mock import AsyncMock, patch

import pytest

from documents.factories import DocumentFactory
from documents.models import Document
from documents.tasks import (
    enqueue_document_processing,
    process_document_task,
)


@pytest.mark.django_db(transaction=True)
class TestRunMockAgentInBackground:
    def test_success_path_runs_ingestion_then_agent(self):
        document = DocumentFactory()

        with (
            patch("documents.tasks.ingest_document") as mock_ingest,
            patch("documents.tasks.trigger_agent_run", AsyncMock()) as mock_trigger,
        ):
            process_document_task(document.id)

        mock_ingest.assert_called_once_with(document)
        mock_trigger.assert_awaited_once_with(document.id)

        # Document status untouched by this function on the success path --
        # trigger_agent_run itself owns setting it.
        document.refresh_from_db()
        assert document.status == Document.Status.PENDING

    def test_ingestion_failure_does_not_block_agent_run(self):
        document = DocumentFactory()

        with (
            patch(
                "documents.tasks.ingest_document",
                side_effect=RuntimeError("chroma exploded"),
            ),
            patch("documents.tasks.trigger_agent_run", AsyncMock()) as mock_trigger,
        ):
            process_document_task(document.id)

        mock_trigger.assert_awaited_once_with(document.id)

    def test_total_agent_failure_marks_document_failed(self):
        document = DocumentFactory()

        with (
            patch("documents.tasks.ingest_document"),
            patch(
                "documents.tasks.trigger_agent_run",
                AsyncMock(side_effect=RuntimeError("both paths failed")),
            ),
        ):
            process_document_task(document.id)

        document.refresh_from_db()
        assert document.status == Document.Status.FAILED

    def test_document_not_found_is_logged_and_does_not_raise(self):
        fake_id = uuid.uuid4()

        # Should not raise -- the lookup failure must be caught and logged.
        process_document_task(fake_id)

    def test_enqueue_document_processing_pushes_to_rq(self):
        document = DocumentFactory()

        with patch("documents.tasks.process_document_task.delay") as mock_delay:
            result = enqueue_document_processing(str(document.id))

            assert result is True
            mock_delay.assert_called_once_with(str(document.id))
