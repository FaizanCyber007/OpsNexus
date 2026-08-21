"""Pytest root configuration and fixtures for OpsNexus."""

import os
import pytest
from django.core.cache import cache


def pytest_configure(config):
    """Ensure in-memory SQLite database is used for fast, isolated test execution."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"


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
