import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.factories import OrganizationFactory, UserFactory, UserProfileFactory
from core.models import HealthRule, UserProfile

User = get_user_model()


@pytest.fixture
def auth_user(db):
    user = UserFactory()
    org = OrganizationFactory()
    UserProfileFactory(user=user, organization=org, role=UserProfile.Role.ADMIN)
    return user, org


@pytest.fixture
def api_client(auth_user):
    user, org = auth_user
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestHealthRuleViewSet:
    def test_list_health_rules(self, api_client, auth_user):
        _, org = auth_user
        HealthRule.objects.create(
            organization=org,
            name="Latency Rule",
            metric="latency_p99",
            threshold=250.0,
        )

        response = api_client.get("/api/v1/health-rules/")
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert response.data[0]["name"] == "Latency Rule"

    def test_create_health_rule(self, api_client, auth_user):
        _, org = auth_user
        payload = {
            "organization": str(org.id),
            "name": "CPU High",
            "metric": "cpu_usage",
            "threshold": 85.0,
            "is_active": True,
        }
        response = api_client.post("/api/v1/health-rules/", payload)
        assert response.status_code == 201
        assert response.data["name"] == "CPU High"


@pytest.mark.django_db
class TestPlaybookViewSet:
    def test_list_and_create_playbooks(self, api_client, auth_user):
        _, org = auth_user
        payload = {
            "organization": str(org.id),
            "name": "Vendor Escalation Protocol",
            "description": "Triggered on critical security findings",
            "content": "Step 1: Notify CISO. Step 2: Quarantine vendor access.",
            "is_active": True,
        }
        response = api_client.post("/api/v1/playbooks/", payload)
        assert response.status_code == 201
        assert response.data["name"] == "Vendor Escalation Protocol"

        list_resp = api_client.get("/api/v1/playbooks/")
        assert list_resp.status_code == 200
        assert len(list_resp.data) >= 1


@pytest.mark.django_db
class TestSystemStatusView:
    def test_system_status_returns_operational(self, api_client, auth_user):
        user, _ = auth_user
        user.is_staff = True
        user.save()
        response = api_client.get("/api/v1/system/status/")
        assert response.status_code == 200
        assert response.data["status"] == "operational"
        assert "components" in response.data
        assert "supervisor_llm" in response.data["components"]
        assert "worker_llm" in response.data["components"]
        assert "vector_memory" in response.data["components"]
