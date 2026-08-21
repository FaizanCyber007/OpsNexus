"""Pytest root configuration and fixtures for OpsNexus."""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def configure_test_cache(settings):
    """Ensure in-memory cache backend is used during testing."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "opsnexus-test-locmem",
        }
    }
    cache.clear()
    yield
    cache.clear()
