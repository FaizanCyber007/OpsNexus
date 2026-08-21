"""Custom DRF Rate Throttling Classes for OpsNexus."""

from rest_framework.throttling import UserRateThrottle


class DocumentUploadRateThrottle(UserRateThrottle):
    """Stricter rate throttle specifically for document uploads (5 requests/minute)."""

    scope = "document_upload"


class ChatRateThrottle(UserRateThrottle):
    """Stricter rate throttle for LangGraph RAG document chat & arena queries (5 requests/minute)."""  # noqa: E501

    scope = "chat"
