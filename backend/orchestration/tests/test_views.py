import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rest_framework.test import APIClient

from documents.factories import DocumentFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestDocumentChatEndpoint:
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
        assert data["result"]["execution_time_ms"] >= 1
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
        assert data["faster_model"] in ("groq", "gemini")
        assert "time_diff_ms" in data

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
