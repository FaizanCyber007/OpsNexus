"""Audit log context middleware for OpsNexus.

Uses contextvars to maintain thread-safe and async-safe access to the
current authenticated user and client IP address across Django signals
and background tasks for SOC2 audit logging.
"""

from contextvars import ContextVar
from typing import Any

from django.conf import settings

_current_user: ContextVar[Any] = ContextVar("current_user", default=None)
_client_ip: ContextVar[str | None] = ContextVar("client_ip", default=None)


def get_current_user() -> Any:
    """Retrieve the current user from context."""
    return _current_user.get()


def get_client_ip() -> str | None:
    """Retrieve the client IP address from context."""
    return _client_ip.get()


def set_audit_context(user: Any = None, ip_address: str | None = None):
    """Context manager / helper to explicitly set audit context."""
    token_user = _current_user.set(user)
    token_ip = _client_ip.set(ip_address)
    return token_user, token_ip


def reset_audit_context(tokens: tuple[Any, Any]):
    """Reset context tokens."""
    _current_user.reset(tokens[0])
    _client_ip.reset(tokens[1])


def _extract_client_ip(request: Any) -> str | None:
    """Extract client IP address handling proxies and direct connections."""
    num_proxies = getattr(settings, "NUM_PROXIES", 0)
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if num_proxies > 0 and x_forwarded_for:
        ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        if len(ips) >= num_proxies:
            return ips[-num_proxies]
    return request.META.get("REMOTE_ADDR")


class AuditLogContextMiddleware:
    """Middleware capturing user and IP context for SOC2 audit logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        ip = _extract_client_ip(request)

        token_user = _current_user.set(
            user if (user and user.is_authenticated) else None
        )
        token_ip = _client_ip.set(ip)

        try:
            response = self.get_response(request)
            return response
        finally:
            _current_user.reset(token_user)
            _client_ip.reset(token_ip)


class AuditLogContextMixin:
    """DRF View/ViewSet mixin to initialize audit user context after authentication."""

    def initial(self, request, *args, **kwargs):
        initial_func = getattr(super(), "initial", None)
        if callable(initial_func):
            initial_func(request, *args, **kwargs)
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            _current_user.set(user)
