import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from agents.factories import AgentProfileFactory, AgentRunFactory
from documents.factories import DocumentFactory

User = get_user_model()


@pytest.fixture
def auth_user(db):
    return User.objects.create_superuser(
        username="superadmin", password="password", email="super@example.com"
    )


@pytest.fixture
def api_client(auth_user):
    client = APIClient()
    client.force_authenticate(user=auth_user)
    return client


@pytest.mark.django_db
class TestAgentProfileViewSet:
    def test_list_agent_profiles(self, api_client):
        AgentProfileFactory(name="Supervisor Profile")
        response = api_client.get("/api/v1/agent-profiles/")
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert any(p["name"] == "Supervisor Profile" for p in response.data)


@pytest.mark.django_db
class TestAgentRunListAndDetail:
    def test_list_agent_runs(self, api_client):
        doc = DocumentFactory()
        run = AgentRunFactory(document=doc)
        response = api_client.get("/api/v1/agent-runs/")
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert any(r["id"] == str(run.id) for r in response.data)

    def test_get_agent_run_detail(self, api_client):
        doc = DocumentFactory()
        run = AgentRunFactory(document=doc)
        response = api_client.get(f"/api/v1/agent-runs/{run.id}/")
        assert response.status_code == 200
        assert response.data["id"] == str(run.id)


@pytest.mark.django_db
class TestMCPToolsView:
    def test_list_mcp_tools(self, api_client):
        response = api_client.get("/api/v1/mcp-tools/")
        assert response.status_code == 200
        assert "tools" in response.data
        assert any(
            t["name"] == "get_internal_pricing_policy" for t in response.data["tools"]
        )

    def test_test_invoke_pricing_tool(self, api_client):
        response = api_client.post(
            "/api/v1/mcp-tools/",
            {"tool_name": "get_internal_pricing_policy"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert "currency" in response.data["result"]
