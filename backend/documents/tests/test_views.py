from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from agents.factories import AgentRunFactory, AnswerFactory
from core.factories import OrganizationFactory
from core.models import UserProfile
from documents.factories import DocumentFactory
from documents.models import Document

User = get_user_model()


@pytest.fixture
def auth_context(db):
    org = OrganizationFactory()
    user = User.objects.create_user(  # type: ignore
        username="member_user", password="password", email="member@example.com"
    )
    profile = UserProfile.objects.create(
        user=user, organization=org, role=UserProfile.Role.MEMBER
    )
    return {"user": user, "organization": org, "profile": profile}


@pytest.fixture
def api_client(auth_context):
    client = APIClient()
    client.force_authenticate(user=auth_context["user"])
    return client


@pytest.mark.django_db
class TestDocumentUploadEndpoint:
    def test_upload_with_file_returns_202_and_creates_document(
        self, api_client, auth_context
    ):
        organization = auth_context["organization"]
        upload = SimpleUploadedFile(
            "rfp_questionnaire.txt",
            b"Please describe your security practices.",
            content_type="text/plain",
        )

        with (
            patch("documents.views.enqueue_document_processing") as MockEnqueue,
            patch("django.db.transaction.on_commit", side_effect=lambda func: func()),
        ):
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

        document = Document.objects.get(id=response.data["document_id"])
        MockEnqueue.assert_called_once_with(document.id)
        assert document.organization_id == organization.id
        assert document.file is not None
        assert "rfp_questionnaire" in document.file.name
        assert str(document.file.name).endswith(".txt")
        assert document.file_path == document.file.name
        assert document.status == Document.Status.PENDING

    def test_upload_without_file_still_succeeds(self, api_client, auth_context):
        organization = auth_context["organization"]

        with patch("documents.views.enqueue_document_processing"):
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

        with patch("documents.views.enqueue_document_processing"):
            response = api_client.post(
                "/api/documents/",
                {"doc_type": Document.DocType.OTHER, "file": upload},
                format="multipart",
            )

        assert response.status_code == 400
        assert not Document.objects.exists()

    def test_upload_invalid_organization_returns_400(self, api_client):
        upload = SimpleUploadedFile("f.txt", b"content", content_type="text/plain")

        with patch("documents.views.enqueue_document_processing"):
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

    def test_upload_to_another_organization_forbidden(self, api_client):
        other_org = OrganizationFactory()
        upload = SimpleUploadedFile("f.txt", b"content", content_type="text/plain")

        with patch("documents.views.enqueue_document_processing"):
            response = api_client.post(
                "/api/documents/",
                {
                    "organization": str(other_org.id),
                    "doc_type": Document.DocType.OTHER,
                    "file": upload,
                },
                format="multipart",
            )

        assert response.status_code == 400
        assert "organization" in response.data

    def test_upload_enqueues_background_task_targeting_the_new_document(
        self, api_client, auth_context
    ):
        organization = auth_context["organization"]
        upload = SimpleUploadedFile("f.txt", b"content", content_type="text/plain")

        with (
            patch("documents.views.enqueue_document_processing") as MockEnqueue,
            patch("django.db.transaction.on_commit", side_effect=lambda func: func()),
        ):
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
        MockEnqueue.assert_called_once_with(document_id)


@pytest.mark.django_db
class TestDocumentListEndpoint:
    def test_orders_newest_first(self, api_client, auth_context):
        organization = auth_context["organization"]
        older = DocumentFactory(organization=organization)
        newer = DocumentFactory(organization=organization)

        response = api_client.get("/api/documents/")

        assert response.status_code == 200
        ids = [doc["id"] for doc in response.data]
        assert ids.index(str(newer.id)) < ids.index(str(older.id))

    def test_filters_by_organization_query_param(self, api_client, auth_context):
        org_a = auth_context["organization"]
        org_b = OrganizationFactory()
        doc_a = DocumentFactory(organization=org_a)
        DocumentFactory(organization=org_b)

        response = api_client.get(f"/api/documents/?organization={org_a.id}")

        assert response.status_code == 200
        assert [doc["id"] for doc in response.data] == [str(doc_a.id)]

    def test_excludes_other_organization_documents(self, api_client, auth_context):
        org_a = auth_context["organization"]
        org_b = OrganizationFactory()
        doc_a = DocumentFactory(organization=org_a)
        DocumentFactory(organization=org_b)

        response = api_client.get("/api/documents/")

        assert response.status_code == 200
        ids = [doc["id"] for doc in response.data]
        assert str(doc_a.id) in ids
        assert len(ids) == 1

    def test_excludes_soft_deleted_documents(self, api_client, auth_context):
        organization = auth_context["organization"]
        document = DocumentFactory(organization=organization)

        api_client.delete(f"/api/documents/{document.id}/")
        response = api_client.get("/api/documents/")

        assert response.status_code == 200
        assert response.data == []


@pytest.mark.django_db
class TestDocumentRetrieveEndpoint:
    def test_returns_the_document(self, api_client, auth_context):
        organization = auth_context["organization"]
        document = DocumentFactory(organization=organization)

        response = api_client.get(f"/api/documents/{document.id}/")

        assert response.status_code == 200
        assert response.data["id"] == str(document.id)

    def test_cannot_retrieve_other_organization_document(self, api_client):
        other_org = OrganizationFactory()
        document = DocumentFactory(organization=other_org)

        response = api_client.get(f"/api/documents/{document.id}/")

        assert response.status_code == 404

    def test_soft_deleted_document_returns_404(self, api_client, auth_context):
        organization = auth_context["organization"]
        document = DocumentFactory(organization=organization)

        api_client.delete(f"/api/documents/{document.id}/")
        response = api_client.get(f"/api/documents/{document.id}/")

        assert response.status_code == 404


@pytest.mark.django_db
class TestDocumentDestroyEndpoint:
    def test_soft_deletes_instead_of_removing_the_row(self, api_client, auth_context):
        organization = auth_context["organization"]
        document = DocumentFactory(organization=organization)

        response = api_client.delete(f"/api/documents/{document.id}/")

        assert response.status_code == 204
        assert Document.objects.filter(id=document.id).exists()

        document.refresh_from_db()
        assert document.deleted_at is not None

    def test_cannot_delete_other_organization_document(self, api_client):
        other_org = OrganizationFactory()
        document = DocumentFactory(organization=other_org)

        response = api_client.delete(f"/api/documents/{document.id}/")

        assert response.status_code == 404

    def test_deleting_nonexistent_document_returns_404(self, api_client):
        response = api_client.delete(
            "/api/documents/00000000-0000-0000-0000-000000000000/"
        )

        assert response.status_code == 404

    def test_deleting_already_deleted_document_returns_404(
        self, api_client, auth_context
    ):
        organization = auth_context["organization"]
        document = DocumentFactory(organization=organization)

        api_client.delete(f"/api/documents/{document.id}/")
        response = api_client.delete(f"/api/documents/{document.id}/")

        assert response.status_code == 404


@pytest.mark.django_db
class TestDocumentAnswersEndpoint:
    def test_returns_answers_for_the_document(self, api_client, auth_context):
        organization = auth_context["organization"]
        document = DocumentFactory(organization=organization)
        agent_run = AgentRunFactory(document=document)
        answer = AnswerFactory(agent_run=agent_run, content="A real answer.")

        response = api_client.get(f"/api/documents/{document.id}/answers/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(answer.id)
        assert response.data[0]["content"] == "A real answer."

    def test_cannot_view_answers_for_other_organization_document(self, api_client):
        other_org = OrganizationFactory()
        document = DocumentFactory(organization=other_org)
        agent_run = AgentRunFactory(document=document)
        AnswerFactory(agent_run=agent_run, content="Secret answer.")

        response = api_client.get(f"/api/documents/{document.id}/answers/")

        assert response.status_code == 404

    def test_returns_empty_list_when_no_answers_exist(self, api_client, auth_context):
        organization = auth_context["organization"]
        document = DocumentFactory(organization=organization)

        response = api_client.get(f"/api/documents/{document.id}/answers/")

        assert response.status_code == 200
        assert response.data == []

    def test_soft_deleted_document_returns_404(self, api_client, auth_context):
        organization = auth_context["organization"]
        document = DocumentFactory(organization=organization)

        api_client.delete(f"/api/documents/{document.id}/")
        response = api_client.get(f"/api/documents/{document.id}/answers/")

        assert response.status_code == 404

    def test_malformed_document_id_returns_404(self, api_client):
        response = api_client.get("/api/documents/not-a-valid-uuid/answers/")

        assert response.status_code == 404

    def test_answers_query_optimized_with_select_related(
        self, api_client, auth_context, django_assert_num_queries
    ):
        organization = auth_context["organization"]
        document = DocumentFactory(organization=organization)
        agent_run = AgentRunFactory(document=document)
        for i in range(5):
            AnswerFactory(agent_run=agent_run, content=f"Answer {i}")

        with django_assert_num_queries(3):
            response = api_client.get(f"/api/documents/{document.id}/answers/")
            assert response.status_code == 200
            assert len(response.data) == 5


@pytest.mark.django_db
class TestDocumentChatTenantIsolation:
    def test_cannot_chat_with_other_organization_document(self, api_client):
        other_org = OrganizationFactory()
        document = DocumentFactory(organization=other_org)

        response = api_client.post(
            f"/api/documents/{document.id}/chat/",
            {"question": "What is the policy?"},
            format="json",
        )

        assert response.status_code == 404
