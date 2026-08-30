from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from core.factories import OrganizationFactory, UserFactory, UserProfileFactory
from core.models import UserProfile
from documents.factories import DocumentFactory
from documents.models import Document
from orchestration.model_client import SUPERVISOR_MODEL_NAME


@pytest.fixture(autouse=True)
def reset_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def auth_client():
    org = OrganizationFactory()
    user = UserFactory()
    UserProfileFactory(user=user, organization=org, role=UserProfile.Role.MEMBER)
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user, org


@pytest.mark.django_db
class TestRateLimitingThrottling:
    def test_document_upload_throttled_at_5_requests_per_minute(self, auth_client):
        """Verify 429 Too Many Requests status code when upload throttle is exceeded."""

        client, _, org = auth_client

        with patch("documents.views.enqueue_document_processing"):
            # First 5 requests should succeed (202 Accepted)
            for i in range(5):
                file_obj = SimpleUploadedFile(
                    f"test_doc_{i}.txt",
                    b"Document content for throttling test.",
                    content_type="text/plain",
                )
                response = client.post(
                    "/api/v1/documents/",
                    {
                        "organization": str(org.id),
                        "doc_type": Document.DocType.OTHER,
                        "file": file_obj,
                    },
                    format="multipart",
                )
                assert (
                    response.status_code == 202
                ), f"Request {i+1} failed with {response.status_code}: {response.data}"

            # 6th request within the minute window must return 429 Too Many Requests
            file_obj_throttled = SimpleUploadedFile(
                "throttled.txt",
                b"This upload should be throttled.",
                content_type="text/plain",
            )
            response_throttled = client.post(
                "/api/v1/documents/",
                {
                    "organization": str(org.id),
                    "doc_type": Document.DocType.OTHER,
                    "file": file_obj_throttled,
                },
                format="multipart",
            )
            assert response_throttled.status_code == 429
            assert "throttled" in str(response_throttled.data.get("detail", "")).lower()

    def test_document_chat_throttled_at_5_requests_per_minute(self, auth_client):
        """Verifies 429 Too Many Requests status code when chat throttle is exceeded."""
        client, _, org = auth_client
        document = DocumentFactory(organization=org)

        mock_result = {
            "compare": False,
            "question": "What is the policy?",
            "retrieved_context": [],
            "result": {
                "model_name": f"Gemini Flash ({SUPERVISOR_MODEL_NAME})",
                "provider": "gemini",
                "response": "Policy terms verified.",
                "execution_time_ms": 150,
                "status": "success",
                "is_simulated": True,
            },
        }

        with patch(
            "orchestration.views._execute_chat_routing",
            return_value=mock_result,
        ):
            # First 5 chat requests succeed (200 OK)
            for i in range(5):
                res = client.post(
                    f"/api/v1/documents/{document.id}/chat/",
                    {"question": f"Question {i}?", "compare": False},
                    format="json",
                )
                assert (
                    res.status_code == 200
                ), f"Chat request {i+1} failed with {res.status_code}: {res.data}"

            # 6th request within the minute window must return 429 Too Many Requests
            res_throttled = client.post(
                f"/api/v1/documents/{document.id}/chat/",
                {"question": "Throttled question?", "compare": False},
                format="json",
            )
            assert res_throttled.status_code == 429
            assert "throttled" in str(res_throttled.data.get("detail", "")).lower()


@pytest.mark.django_db
class TestSecurityHeaders:
    def test_production_security_settings_configured(self):
        """Verify required Django security configuration settings."""
        assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
        assert settings.X_FRAME_OPTIONS == "DENY"
        assert settings.CSRF_COOKIE_HTTPONLY is True

    def test_security_headers_present_in_responses(self, auth_client):
        """Verify security headers are attached to HTTP responses by middleware."""
        client, _, _ = auth_client
        response = client.get("/api/v1/documents/")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"


class TestClientIPExtraction:
    def test_extract_client_ip_without_proxies_uses_remote_addr(self, rf):
        from core.middleware import _extract_client_ip

        request = rf.get(
            "/api/v1/documents/",
            HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2",
            REMOTE_ADDR="3.3.3.3",
        )
        with patch.object(settings, "NUM_PROXIES", 0):
            assert _extract_client_ip(request) == "3.3.3.3"

    def test_extract_client_ip_with_one_trusted_proxy(self, rf):
        from core.middleware import _extract_client_ip

        request = rf.get(
            "/api/v1/documents/",
            HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2",
            REMOTE_ADDR="3.3.3.3",
        )
        with patch.object(settings, "NUM_PROXIES", 1):
            assert _extract_client_ip(request) == "2.2.2.2"

    def test_extract_client_ip_with_two_trusted_proxies(self, rf):
        from core.middleware import _extract_client_ip

        request = rf.get(
            "/api/v1/documents/",
            HTTP_X_FORWARDED_FOR="spoofed_client, real_client, proxy1",
            REMOTE_ADDR="proxy2",
        )
        with patch.object(settings, "NUM_PROXIES", 2):
            assert _extract_client_ip(request) == "real_client"
