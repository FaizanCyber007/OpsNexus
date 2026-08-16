from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from agents.factories import AgentRunFactory, AnswerFactory
from core.factories import OrganizationFactory
from documents.factories import DocumentFactory
from documents.models import Document


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestDocumentUploadEndpoint:
    def test_upload_with_file_returns_202_and_creates_document(self, api_client):
        organization = OrganizationFactory()
        upload = SimpleUploadedFile(
            "rfp_questionnaire.txt",
            b"Please describe your security practices.",
            content_type="text/plain",
        )

        with patch("documents.views.threading.Thread") as MockThread:
            response = api_client.post(
                "/api/documents/",
                {
                    "organization": str(organization.id),
                    "doc_type": Document.DocType.SECURITY_QUESTIONNAIRE,
                    "file": upload,
                },
                format="multipart",
            )

        assert response.status_code == 202
        assert response.data["status"] == "processing"
        MockThread.assert_called_once()
        MockThread.return_value.start.assert_called_once()

        document = Document.objects.get(id=response.data["document_id"])
        assert document.organization_id == organization.id
        # Storage may append a random suffix if a same-named file already
        # exists on disk, so check the stem + extension rather than an exact
        # filename match.
        assert "rfp_questionnaire" in document.file.name
        assert document.file.name.endswith(".txt")
        assert document.file_path == document.file.name
        assert document.status == Document.Status.PENDING

    def test_upload_without_file_still_succeeds(self, api_client):
        organization = OrganizationFactory()

        with patch("documents.views.threading.Thread"):
            response = api_client.post(
                "/api/documents/",
                {
                    "organization": str(organization.id),
                    "doc_type": Document.DocType.OTHER,
                },
                format="multipart",
            )

        assert response.status_code == 202
        document = Document.objects.get(id=response.data["document_id"])
        assert not document.file
        assert document.file_path == ""

    def test_upload_missing_organization_returns_400(self, api_client):
        upload = SimpleUploadedFile("f.txt", b"content", content_type="text/plain")

        with patch("documents.views.threading.Thread"):
            response = api_client.post(
                "/api/documents/",
                {"doc_type": Document.DocType.OTHER, "file": upload},
                format="multipart",
            )

        assert response.status_code == 400
        assert not Document.objects.exists()

    def test_upload_invalid_organization_returns_400(self, api_client):
        upload = SimpleUploadedFile("f.txt", b"content", content_type="text/plain")

        with patch("documents.views.threading.Thread"):
            response = api_client.post(
                "/api/documents/",
                {
                    "organization": "00000000-0000-0000-0000-000000000000",
                    "doc_type": Document.DocType.OTHER,
                    "file": upload,
                },
                format="multipart",
            )

        assert response.status_code == 400

    def test_upload_spawns_background_thread_targeting_the_new_document(
        self, api_client
    ):
        organization = OrganizationFactory()
        upload = SimpleUploadedFile("f.txt", b"content", content_type="text/plain")

        with patch("documents.views.threading.Thread") as MockThread:
            response = api_client.post(
                "/api/documents/",
                {
                    "organization": str(organization.id),
                    "doc_type": Document.DocType.OTHER,
                    "file": upload,
                },
                format="multipart",
            )

        document_id = response.data["document_id"]
        _, kwargs = MockThread.call_args
        assert kwargs["args"] == (document_id,)
        assert kwargs["daemon"] is True


@pytest.mark.django_db
class TestDocumentListEndpoint:
    def test_orders_newest_first(self, api_client):
        organization = OrganizationFactory()
        older = DocumentFactory(organization=organization)
        newer = DocumentFactory(organization=organization)

        response = api_client.get("/api/documents/")

        assert response.status_code == 200
        ids = [doc["id"] for doc in response.data]
        assert ids.index(str(newer.id)) < ids.index(str(older.id))

    def test_filters_by_organization_query_param(self, api_client):
        org_a = OrganizationFactory()
        org_b = OrganizationFactory()
        doc_a = DocumentFactory(organization=org_a)
        DocumentFactory(organization=org_b)

        response = api_client.get(f"/api/documents/?organization={org_a.id}")

        assert response.status_code == 200
        assert [doc["id"] for doc in response.data] == [str(doc_a.id)]

    def test_excludes_soft_deleted_documents(self, api_client):
        document = DocumentFactory()

        api_client.delete(f"/api/documents/{document.id}/")
        response = api_client.get("/api/documents/")

        assert response.status_code == 200
        assert response.data == []

    def test_no_organization_param_returns_all(self, api_client):
        DocumentFactory()
        DocumentFactory()

        response = api_client.get("/api/documents/")

        assert response.status_code == 200
        assert len(response.data) == 2


@pytest.mark.django_db
class TestDocumentRetrieveEndpoint:
    def test_returns_the_document(self, api_client):
        document = DocumentFactory()

        response = api_client.get(f"/api/documents/{document.id}/")

        assert response.status_code == 200
        assert response.data["id"] == str(document.id)

    def test_soft_deleted_document_returns_404(self, api_client):
        document = DocumentFactory()

        api_client.delete(f"/api/documents/{document.id}/")
        response = api_client.get(f"/api/documents/{document.id}/")

        assert response.status_code == 404


@pytest.mark.django_db
class TestDocumentDestroyEndpoint:
    def test_soft_deletes_instead_of_removing_the_row(self, api_client):
        document = DocumentFactory()

        response = api_client.delete(f"/api/documents/{document.id}/")

        assert response.status_code == 204
        assert Document.objects.filter(id=document.id).exists()

        document.refresh_from_db()
        assert document.deleted_at is not None

    def test_deleting_nonexistent_document_returns_404(self, api_client):
        response = api_client.delete(
            "/api/documents/00000000-0000-0000-0000-000000000000/"
        )

        assert response.status_code == 404

    def test_deleting_already_deleted_document_returns_404(self, api_client):
        document = DocumentFactory()

        api_client.delete(f"/api/documents/{document.id}/")
        response = api_client.delete(f"/api/documents/{document.id}/")

        assert response.status_code == 404


@pytest.mark.django_db
class TestDocumentAnswersEndpoint:
    def test_returns_answers_for_the_document(self, api_client):
        document = DocumentFactory()
        agent_run = AgentRunFactory(document=document)
        answer = AnswerFactory(agent_run=agent_run, content="A real answer.")

        response = api_client.get(f"/api/documents/{document.id}/answers/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(answer.id)
        assert response.data[0]["content"] == "A real answer."

    def test_returns_empty_list_when_no_answers_exist(self, api_client):
        document = DocumentFactory()

        response = api_client.get(f"/api/documents/{document.id}/answers/")

        assert response.status_code == 200
        assert response.data == []
