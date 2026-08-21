from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from agents.models import AgentProfile, AgentRun, Answer, ToolCall
from core.factories import OrganizationFactory
from core.models import UserProfile
from documents.models import Document
from orchestration.agent_runner import AGENT_PROFILE_DEFAULTS, AGENT_PROFILE_NAME

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def reset_llm_api_keys(monkeypatch):
    """Ensure tests run simulated fallbacks by default without live network calls."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def mock_chroma_globally():
    """Mock ChromaDB semantic search and embeddings globally in E2E tests for speed."""
    default_chunks = [
        {
            "text": "Section 1: Data Encryption in transit and at rest using AES-256.",
            "metadata": {"source": "e2e_test"},
            "distance": 0.05,
        }
    ]
    with (
        patch(
            "orchestration.views.ChromaDBClient.semantic_search",
            return_value=default_chunks,
        ),
        patch("memory.vector_client.ChromaDBClient"),
        patch("memory.vector_client._get_embeddings"),
    ):
        yield


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_context():
    org = OrganizationFactory(name="OpsNexus Enterprise Org", slug="opsnexus-ent")
    user = User.objects.create_user(
        username="lead_qa_user",
        email="lead_qa@opsnexus.ai",
        password="secure_password_123",
    )
    profile = UserProfile.objects.create(
        user=user, organization=org, role=UserProfile.Role.ADMIN
    )
    return {"organization": org, "user": user, "profile": profile}


@pytest.mark.django_db
class TestFullPipelineHttpE2E:
    """Comprehensive HTTP End-to-End Test Suite for OpsNexus platform."""

    def test_full_pipeline_happy_path_sales_rfp_flow(self, api_client, auth_context):
        """Execute the exact 5-step Happy Path flow:
        1. Authenticate / Retrieve Mock API Key or User Session.
        2. Send a POST request to upload a mock document.
        3. Verify the background task/agent runner is triggered.
        4. Send a POST request to the /chat/ endpoint for that document.
        5. Assert the final API returns a 200 OK with the proper structured JSON schema.
        """
        org = auth_context["organization"]
        user = auth_context["user"]

        # -------------------------------------------------------------
        # Step 1: Authenticate / Retrieve User Session or API Key
        # -------------------------------------------------------------
        api_client.force_authenticate(user=user)
        api_client.credentials(
            HTTP_AUTHORIZATION="Bearer opsnexus-mock-api-key-live-e2e"
        )

        # -------------------------------------------------------------
        # Step 2: Send a POST request to upload a mock document
        # -------------------------------------------------------------
        mock_file_content = (
            b"OpsNexus Security Questionnaire and RFP Response.\n"
            b"Section 1: Data Encryption in transit and at rest using AES-256.\n"
            b"Section 2: SOC2 Type II Certified with continuous compliance.\n"
            b"Section 3: Standard SLA 99.99% uptime with 4-hour support."
        )
        upload = SimpleUploadedFile(
            "enterprise_security_rfp_questionnaire.txt",
            mock_file_content,
            content_type="text/plain",
        )

        with (
            patch("documents.views.threading.Thread") as MockThread,
            patch("django.db.transaction.on_commit", side_effect=lambda func: func()),
        ):
            upload_response = api_client.post(
                "/api/v1/documents/",
                {
                    "organization": str(org.id),
                    "doc_type": Document.DocType.SECURITY_QUESTIONNAIRE,
                    "file": upload,
                },
                format="multipart",
            )

        # -------------------------------------------------------------
        # Step 3: Verify the background task / agent runner is triggered
        # -------------------------------------------------------------
        assert upload_response.status_code == 202
        assert upload_response.data["status"] == "processing"
        document_id = upload_response.data["document_id"]
        assert document_id is not None

        # Verify background Thread was initialized and started with correct args
        MockThread.assert_called_once()
        _, kwargs = MockThread.call_args
        assert kwargs["args"] == (document_id,)
        assert kwargs["daemon"] is True
        MockThread.return_value.start.assert_called_once()

        # Verify initial document row state in database
        document = Document.objects.get(id=document_id)
        assert document.organization_id == org.id
        assert document.status == Document.Status.PENDING
        assert "enterprise_security_rfp_questionnaire" in document.file.name

        # Simulate background processing completion and record creation
        agent_profile, _ = AgentProfile.objects.get_or_create(
            name=AGENT_PROFILE_NAME,
            defaults=AGENT_PROFILE_DEFAULTS,
        )
        agent_run = AgentRun.objects.create(
            document=document,
            agent_profile=agent_profile,
            status=AgentRun.Status.SUCCEEDED,
            started_at=timezone.now(),
            finished_at=timezone.now(),
        )

        ToolCall.objects.create(
            agent_run=agent_run,
            tool_name="langgraph_supervisor_classify",
            input_data={"document_id": str(document_id)},
            output_data={
                "route": "sales_rfp",
                "reasoning": "RFP security questionnaire.",
            },
        )

        ToolCall.objects.create(
            agent_run=agent_run,
            tool_name="search_company_knowledge",
            input_data={"query": "SOC2 security"},
            output_data={"result": "Found SOC2 Type II certification data."},
        )

        answer = Answer.objects.create(
            agent_run=agent_run,
            question_text="Draft a response to this RFP/questionnaire.",
            content=(
                "OpsNexus complies with SOC2 Type II and utilizes AES-256 encryption. "
                "The SLA guarantees 99.99% availability with 4-hour response."
            ),
            executive_summary=(
                "Enterprise-ready security posture with SOC2 Type II compliance."
            ),
            risk_flags=["Quarterly audit renewal pending"],
            action_items=[
                "Provide SOC2 Type II report to prospect",
                "Confirm SLA addendum",
            ],
            confidence_score=0.96,
            is_verified=False,
        )

        document.status = Document.Status.COMPLETED
        document.save(update_fields=["status"])

        # Verify Answers API endpoint returns structured JSON
        answers_response = api_client.get(f"/api/v1/documents/{document_id}/answers/")
        assert answers_response.status_code == 200
        assert len(answers_response.data) == 1
        ans_data = answers_response.data[0]
        assert ans_data["id"] == str(answer.id)
        assert ans_data["confidence_score"] == 0.96
        assert ans_data["risk_flags"] == ["Quarterly audit renewal pending"]
        assert ans_data["action_items"] == [
            "Provide SOC2 Type II report to prospect",
            "Confirm SLA addendum",
        ]
        assert "SOC2 Type II" in ans_data["executive_summary"]

        # Verify Tool Calls API endpoint returns tool execution logs
        tool_calls_response = api_client.get(
            f"/api/v1/agent-runs/{agent_run.id}/tool-calls/"
        )
        assert tool_calls_response.status_code == 200
        assert len(tool_calls_response.data) >= 2
        tool_names = [tc["tool_name"] for tc in tool_calls_response.data]
        assert "langgraph_supervisor_classify" in tool_names
        assert "search_company_knowledge" in tool_names

        # -------------------------------------------------------------
        # Step 4 & 5: Send POST request to /chat/ and assert 200 OK + Schema
        # -------------------------------------------------------------
        # Single-Model Chat Query
        chat_payload = {
            "question": "What encryption standards and SLA terms are guaranteed?",
            "compare": False,
        }

        chat_response = api_client.post(
            f"/api/v1/documents/{document_id}/chat/",
            chat_payload,
            format="json",
        )

        assert chat_response.status_code == 200
        chat_data = chat_response.data

        # Assert structured response schema for single model
        assert chat_data["compare"] is False
        assert chat_data["question"] == chat_payload["question"]
        assert isinstance(chat_data["retrieved_context"], list)
        assert len(chat_data["retrieved_context"]) == 1
        assert "AES-256" in chat_data["retrieved_context"][0]["text"]
        assert chat_data["retrieved_context"][0]["distance"] == 0.05

        assert "result" in chat_data
        result = chat_data["result"]
        assert "model_name" in result
        assert result["provider"] == "gemini"
        assert result["status"] == "success"
        assert isinstance(result["response"], str)
        assert result["execution_time_ms"] > 0

        # Multi-Model Arena Comparison Chat Query (compare=True)
        arena_payload = {
            "question": "Summarize SOC2 compliance and SLA response times.",
            "compare": True,
        }

        arena_response = api_client.post(
            f"/api/v1/documents/{document_id}/chat/",
            arena_payload,
            format="json",
        )

        assert arena_response.status_code == 200
        arena_data = arena_response.data

        # Assert structured response schema for arena comparison
        assert arena_data["compare"] is True
        assert arena_data["question"] == arena_payload["question"]
        assert isinstance(arena_data["retrieved_context"], list)
        assert "results" in arena_data
        assert "groq" in arena_data["results"]
        assert "gemini" in arena_data["results"]

        groq_res = arena_data["results"]["groq"]
        assert groq_res["provider"] == "groq"
        assert groq_res["status"] == "success"
        assert isinstance(groq_res["execution_time_ms"], int)

        gemini_res = arena_data["results"]["gemini"]
        assert gemini_res["provider"] == "gemini"
        assert gemini_res["status"] == "success"
        assert isinstance(gemini_res["execution_time_ms"], int)

        # In simulated mode (no API keys configured in test), faster_model and time_diff_ms are None
        assert arena_data["faster_model"] is None
        assert arena_data["time_diff_ms"] is None

        # -------------------------------------------------------------
        # Step 6: Test Semantic Redis Cache Hit for Chat
        # -------------------------------------------------------------
        # Re-sending identical query must return cached result immediately
        # without running vector search
        cached_chat_response = api_client.post(
            f"/api/v1/documents/{document_id}/chat/",
            chat_payload,
            format="json",
        )
        assert cached_chat_response.status_code == 200
        assert cached_chat_response.data == chat_data

    def test_full_pipeline_invoice_reconciliation_flow(self, api_client, auth_context):
        """End-to-end flow for invoice reconciliation document."""
        org = auth_context["organization"]
        api_client.force_authenticate(user=auth_context["user"])

        upload = SimpleUploadedFile(
            "vendor_invoice_q3.csv",
            b"Item,Qty,Price\nServer Hosting,1,$14500.00\nTotal,,$14500.00",
            content_type="text/csv",
        )

        with (
            patch("documents.views.threading.Thread") as MockThread,
            patch("django.db.transaction.on_commit", side_effect=lambda func: func()),
        ):
            response = api_client.post(
                "/api/documents/",
                {
                    "organization": str(org.id),
                    "doc_type": Document.DocType.INVOICE,
                    "file": upload,
                },
                format="multipart",
            )

        assert response.status_code == 202
        doc_id = response.data["document_id"]
        MockThread.assert_called_once()

        document = Document.objects.get(id=doc_id)
        document.status = Document.Status.COMPLETED
        document.save(update_fields=["status"])

        # Verify chat endpoint responds for this invoice
        chat_res = api_client.post(
            f"/api/documents/{doc_id}/chat/",
            {"question": "What is the total amount due on this invoice?"},
            format="json",
        )
        assert chat_res.status_code == 200
        assert (
            chat_res.data["question"] == "What is the total amount due on this invoice?"
        )
        assert chat_res.data["result"]["status"] == "success"

    def test_full_pipeline_compliance_audit_flow(self, api_client, auth_context):
        """End-to-end flow for compliance log document."""
        org = auth_context["organization"]
        api_client.force_authenticate(user=auth_context["user"])

        upload = SimpleUploadedFile(
            "soc2_audit_access.log",
            b"[2026-08-20 10:00:00] User admin granted root access to cluster-prod-01",
            content_type="text/plain",
        )

        with (
            patch("documents.views.threading.Thread") as MockThread,
            patch("django.db.transaction.on_commit", side_effect=lambda func: func()),
        ):
            response = api_client.post(
                "/api/documents/",
                {
                    "organization": str(org.id),
                    "doc_type": Document.DocType.COMPLIANCE_LOG,
                    "file": upload,
                },
                format="multipart",
            )

        assert response.status_code == 202
        doc_id = response.data["document_id"]
        MockThread.assert_called_once()

        document = Document.objects.get(id=doc_id)
        agent_profile, _ = AgentProfile.objects.get_or_create(
            name=AGENT_PROFILE_NAME,
            defaults=AGENT_PROFILE_DEFAULTS,
        )
        agent_run = AgentRun.objects.create(
            document=document,
            agent_profile=agent_profile,
            status=AgentRun.Status.SUCCEEDED,
        )
        Answer.objects.create(
            agent_run=agent_run,
            question_text="Compliance summary",
            content="Audit logs parsed successfully.",
            executive_summary="SOC2 access review passed.",
            risk_flags=["Root access session lasted > 1 hour"],
            action_items=["Review root session recording with SecOps"],
            confidence_score=0.92,
        )
        document.status = Document.Status.COMPLETED
        document.save(update_fields=["status"])

        # Check answers endpoint
        ans_res = api_client.get(f"/api/documents/{doc_id}/answers/")
        assert ans_res.status_code == 200
        assert len(ans_res.data) >= 1
        assert ans_res.data[0]["executive_summary"] == "SOC2 access review passed."

    def test_full_pipeline_soft_delete_lifecycle_and_cleanup(
        self, api_client, auth_context
    ):
        """Verifies soft-deletion lifecycle, list exclusion, 404 on chat/answers,
        and ChromaDB vector cleanup scheduling to prevent ghost data."""
        org = auth_context["organization"]
        api_client.force_authenticate(user=auth_context["user"])

        upload = SimpleUploadedFile("temp_doc.txt", b"Temporary confidential terms.")

        with (
            patch("documents.views.threading.Thread"),
            patch("django.db.transaction.on_commit", side_effect=lambda func: func()),
        ):
            upload_res = api_client.post(
                "/api/documents/",
                {
                    "organization": str(org.id),
                    "doc_type": Document.DocType.OTHER,
                    "file": upload,
                },
                format="multipart",
            )

        doc_id = upload_res.data["document_id"]
        doc = Document.objects.get(id=doc_id)
        doc.status = Document.Status.COMPLETED
        doc.save(update_fields=["status"])

        # Confirm listed in active documents
        list_res_before = api_client.get(f"/api/documents/?organization={org.id}")
        assert list_res_before.status_code == 200
        doc_ids_before = [d["id"] for d in list_res_before.data]
        assert str(doc_id) in doc_ids_before

        # Execute Soft Delete via DELETE endpoint
        with (
            patch("django.db.transaction.on_commit", side_effect=lambda func: func()),
            patch("memory.vector_client.ChromaDBClient") as MockChroma,
        ):
            delete_res = api_client.delete(f"/api/documents/{doc_id}/")

        assert delete_res.status_code == 204
        MockChroma.return_value.delete_by_document_id.assert_called_once_with(str(doc_id))

        # Verify soft delete in DB
        doc.refresh_from_db()
        assert doc.deleted_at is not None

        # Verify excluded from active list
        list_res_after = api_client.get(f"/api/documents/?organization={org.id}")
        assert list_res_after.status_code == 200
        doc_ids_after = [d["id"] for d in list_res_after.data]
        assert str(doc_id) not in doc_ids_after

        # Verify direct retrieval 404s
        assert api_client.get(f"/api/documents/{doc_id}/").status_code == 404

        # Verify answers endpoint 404s
        assert api_client.get(f"/api/documents/{doc_id}/answers/").status_code == 404

        # Verify chat endpoint 404s
        chat_404_res = api_client.post(
            f"/api/v1/documents/{doc_id}/chat/",
            {"question": "What were the terms?"},
            format="json",
        )
        assert chat_404_res.status_code == 404

    def test_full_pipeline_error_handling_and_validation(
        self, api_client, auth_context
    ):
        """Assert validation errors across upload and chat endpoints."""
        api_client.force_authenticate(user=auth_context["user"])

        # Upload without organization -> 400
        upload = SimpleUploadedFile("test.txt", b"content")
        bad_upload_res = api_client.post(
            "/api/documents/",
            {"doc_type": Document.DocType.OTHER, "file": upload},
            format="multipart",
        )
        assert bad_upload_res.status_code == 400

        # Chat on valid document with empty question -> 400
        org = auth_context["organization"]
        doc = Document.objects.create(organization=org, doc_type=Document.DocType.OTHER)

        empty_q_res = api_client.post(
            f"/api/v1/documents/{doc.id}/chat/",
            {"question": "   "},
            format="json",
        )
        assert empty_q_res.status_code == 400
        assert "question" in empty_q_res.data["error"].lower()

        # Chat on non-existent document ID -> 404
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        not_found_res = api_client.post(
            f"/api/v1/documents/{non_existent_id}/chat/",
            {"question": "Hello?"},
            format="json",
        )
        assert not_found_res.status_code == 404
