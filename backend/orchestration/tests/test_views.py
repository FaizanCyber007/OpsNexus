import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rest_framework.test import APIClient

from documents.factories import DocumentFactory


from django.contrib.auth import get_user_model
from core.models import UserProfile
from core.factories import OrganizationFactory

User = get_user_model()


@pytest.fixture
def auth_context(db):
    user = User.objects.create_superuser(  # type: ignore
        username="admin", password="password", email="admin@example.com"
    )
    return {"user": user}


@pytest.fixture
def api_client(auth_context):
    client = APIClient()
    client.force_authenticate(user=auth_context["user"])
    return client


@pytest.fixture(autouse=True)
def reset_llm_api_keys(monkeypatch):
    """Ensure tests run simulated fallbacks by default without live network calls."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


@pytest.mark.django_db
class TestDocumentChatEndpoint:
    def test_unauthenticated_request_returns_401(self):
        unauth_client = APIClient()
        document = DocumentFactory()
        response = unauth_client.post(
            f"/api/v1/documents/{document.id}/chat/",
            {"question": "What are the payment terms?"},
            format="json",
        )
        assert response.status_code in (401, 403)

    def test_organization_isolation_returns_404(self):
        org_a = OrganizationFactory()
        org_b = OrganizationFactory()
        user_b = User.objects.create_user(username="user_b", password="password")  # type: ignore
        UserProfile.objects.create(user=user_b, organization=org_b)

        doc_a = DocumentFactory(organization=org_a)

        client_b = APIClient()
        client_b.force_authenticate(user=user_b)

        response = client_b.post(
            f"/api/v1/documents/{doc_a.id}/chat/",
            {"question": "Can user B read doc A?"},
            format="json",
        )
        assert response.status_code == 404

    def test_single_model_chat_success(self, api_client):
        document = DocumentFactory(file_path="contracts/master_services.pdf")

        mock_chunks = [
            {
                "text": "Payment terms are Net 30 from invoice receipt.",
                "metadata": {"document_id": str(document.id)},
                "distance": 0.12,
            }
        ]

        with patch(
            "orchestration.views.ChromaDBClient.semantic_search",
            return_value=mock_chunks,
        ):
            response = api_client.post(
                f"/api/v1/documents/{document.id}/chat/",
                {"question": "What are the payment terms?", "compare": False},
                format="json",
            )

        assert response.status_code == 200
        data = response.data
        assert data["compare"] is False
        assert data["question"] == "What are the payment terms?"
        assert len(data["retrieved_context"]) == 1
        assert data["retrieved_context"][0]["text"] == mock_chunks[0]["text"]
        assert "result" in data
        assert data["result"]["status"] == "success"
        assert "execution_time_ms" in data["result"]
        assert data["result"]["execution_time_ms"] >= 0
        assert "response" in data["result"]

    def test_multi_model_comparison_success(self, api_client):
        document = DocumentFactory(file_path="security/soc2_type2.pdf")

        mock_chunks = [
            {
                "text": (
                    "Data is encrypted at rest using AES-256 and in transit "
                    "via TLS 1.3."
                ),
                "metadata": {"document_id": str(document.id)},
                "distance": 0.05,
            }
        ]

        with patch(
            "orchestration.views.ChromaDBClient.semantic_search",
            return_value=mock_chunks,
        ):
            response = api_client.post(
                f"/api/v1/documents/{document.id}/chat/",
                {"question": "What encryption standards are used?", "compare": True},
                format="json",
            )

        assert response.status_code == 200
        data = response.data
        assert data["compare"] is True
        assert data["question"] == "What encryption standards are used?"
        assert len(data["retrieved_context"]) == 1
        assert "results" in data
        assert "groq" in data["results"]
        assert "gemini" in data["results"]
        assert data["results"]["groq"]["status"] == "success"
        assert data["results"]["gemini"]["status"] == "success"
        assert "execution_time_ms" in data["results"]["groq"]
        assert "execution_time_ms" in data["results"]["gemini"]
        # In simulated mode, faster_model and time_diff_ms are null
        assert data["faster_model"] is None
        assert data["time_diff_ms"] is None

    def test_works_via_api_documents_chat_action(self, api_client):
        document = DocumentFactory(file_path="compliance/policy.pdf")

        with patch(
            "orchestration.views.ChromaDBClient.semantic_search",
            return_value=[],
        ):
            response = api_client.post(
                f"/api/documents/{document.id}/chat/",
                {"question": "Summarize policy"},
                format="json",
            )

        assert response.status_code == 200
        assert response.data["question"] == "Summarize policy"

    def test_missing_question_returns_400(self, api_client):
        document = DocumentFactory()

        response = api_client.post(
            f"/api/v1/documents/{document.id}/chat/",
            {"question": "   "},
            format="json",
        )

        assert response.status_code == 400
        assert "question" in response.data["error"].lower()

    def test_nonexistent_document_returns_404(self, api_client):
        random_id = uuid.uuid4()
        response = api_client.post(
            f"/api/v1/documents/{random_id}/chat/",
            {"question": "What is this?"},
            format="json",
        )

        assert response.status_code == 404

    def test_soft_deleted_document_returns_404(self, api_client):
        from django.utils import timezone

        document = DocumentFactory()
        document.deleted_at = timezone.now()
        document.save(update_fields=["deleted_at"])

        response = api_client.post(
            f"/api/v1/documents/{document.id}/chat/",
            {"question": "What is this?"},
            format="json",
        )

        assert response.status_code == 404

    def test_real_llm_invocation_when_keys_present(self, api_client, monkeypatch):
        document = DocumentFactory()
        monkeypatch.setenv("GOOGLE_API_KEY", "mock-google-key")
        monkeypatch.setenv("GROQ_API_KEY", "mock-groq-key")

        mock_llm = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = "Real model generated answer for the question."
        mock_llm.ainvoke = AsyncMock(return_value=mock_resp)

        with (
            patch(
                "orchestration.model_client.LLMFactory.get_supervisor_llm",
                return_value=mock_llm,
            ),
            patch(
                "orchestration.model_client.LLMFactory.get_worker_llm",
                return_value=mock_llm,
            ),
            patch(
                "orchestration.views.ChromaDBClient.semantic_search", return_value=[]
            ),
        ):
            response = api_client.post(
                f"/api/v1/documents/{document.id}/chat/",
                {"question": "Is this compliant?", "compare": True},
                format="json",
            )

        assert response.status_code == 200
        assert (
            response.data["results"]["groq"]["response"]
            == "Real model generated answer for the question."
        )
        assert (
            response.data["results"]["gemini"]["response"]
            == "Real model generated answer for the question."
        )

    def test_exact_same_question_returns_cached_response(self, api_client):
        from django.core.cache import cache

        cache.clear()
        document = DocumentFactory()
        mock_chat_data = {
            "compare": False,
            "question": "What is the return policy?",
            "retrieved_context": [
                {"text": "Cached chunk text", "metadata": {}, "distance": 0.1}
            ],
            "result": {
                "model_name": "Gemini Flash (gemini-2.5-flash)",
                "provider": "gemini",
                "response": "The return policy is 30 days.",
                "execution_time_ms": 150,
                "status": "success",
            },
        }

        with (
            patch(
                "orchestration.views._retrieve_document_context",
                return_value=[
                    {"text": "Cached chunk text", "metadata": {}, "distance": 0.1}
                ],
            ) as mock_retrieve,
            patch(
                "orchestration.views._execute_chat_routing",
                new=AsyncMock(return_value=mock_chat_data),
            ) as mock_exec,
        ):
            # First request (cache miss)
            resp1 = api_client.post(
                f"/api/v1/documents/{document.id}/chat/",
                {"question": "What is the return policy?", "compare": False},
                format="json",
            )
            assert resp1.status_code == 200
            assert mock_retrieve.call_count == 1
            assert mock_exec.call_count == 1

            # Second identical request (cache hit)
            resp2 = api_client.post(
                f"/api/v1/documents/{document.id}/chat/",
                {"question": "What is the return policy?", "compare": False},
                format="json",
            )
            assert resp2.status_code == 200
            # Context retrieval and routing execution are NOT called again
            assert mock_retrieve.call_count == 1
            assert mock_exec.call_count == 1
            assert resp2.data["question"] == resp1.data["question"]
            assert resp2.data["result"]["response"] == resp1.data["result"]["response"]

    def test_different_question_or_document_produces_cache_miss(self, api_client):
        from django.core.cache import cache

        cache.clear()
        doc1 = DocumentFactory()
        doc2 = DocumentFactory()
        mock_chat_data = {
            "compare": False,
            "question": "Sample question",
            "retrieved_context": [],
            "result": {
                "model_name": "Gemini Flash",
                "provider": "gemini",
                "response": "Sample answer",
                "execution_time_ms": 100,
                "status": "success",
            },
        }

        with (
            patch(
                "orchestration.views._retrieve_document_context",
                return_value=[],
            ) as mock_retrieve,
            patch(
                "orchestration.views._execute_chat_routing",
                new=AsyncMock(return_value=mock_chat_data),
            ) as mock_exec,
        ):
            api_client.post(
                f"/api/v1/documents/{doc1.id}/chat/",
                {"question": "Question A"},
                format="json",
            )
            api_client.post(
                f"/api/v1/documents/{doc1.id}/chat/",
                {"question": "Question B"},
                format="json",
            )
            api_client.post(
                f"/api/v1/documents/{doc2.id}/chat/",
                {"question": "Question A"},
                format="json",
            )

            assert mock_retrieve.call_count == 3
            assert mock_exec.call_count == 3


@pytest.mark.django_db
class TestOpenAPISpecification:
    def test_swagger_ui_endpoint_returns_200(self, api_client):
        response = api_client.get("/api/v1/docs/")
        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]
        assert "swagger-ui" in response.content.decode("utf-8").lower()

    def test_redoc_ui_endpoint_returns_200(self, api_client):
        response = api_client.get("/api/v1/redoc/")
        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]

    def test_schema_endpoint_generates_valid_openapi_spec(self, api_client):
        response = api_client.get("/api/v1/schema/")
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "openapi" in content
        assert "OpsNexus API" in content
        assert "/api/v1/documents/" in content
        assert "/chat/" in content
