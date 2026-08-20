import pytest
from rest_framework.test import APIClient

from agents.factories import AgentRunFactory, ToolCallFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestAgentRunToolCallsEndpoint:
    def test_returns_tool_calls_in_chronological_order(self, api_client):
        agent_run = AgentRunFactory()
        first = ToolCallFactory(
            agent_run=agent_run,
            tool_name="langgraph_supervisor_classify",
            input_data={"document_id": "abc"},
            output_data={"route": "sales_rfp", "reasoning": "It's an RFP."},
        )
        second = ToolCallFactory(
            agent_run=agent_run,
            tool_name="search_company_knowledge",
            input_data={"query": "pricing"},
            output_data={"result": "No relevant prior context found."},
        )

        response = api_client.get(f"/api/agent-runs/{agent_run.id}/tool-calls/")

        assert response.status_code == 200
        ids = [call["id"] for call in response.data]
        assert ids == [str(first.id), str(second.id)]

    def test_uses_aliased_field_names(self, api_client):
        agent_run = AgentRunFactory()
        ToolCallFactory(
            agent_run=agent_run,
            tool_name="get_internal_pricing_policy",
            input_data={},
            output_data={"result": "{}"},
        )

        response = api_client.get(f"/api/agent-runs/{agent_run.id}/tool-calls/")

        assert response.status_code == 200
        call = response.data[0]
        assert call["tool_name"] == "get_internal_pricing_policy"
        assert call["tool_input"] == {}
        assert call["tool_output"] == {"result": "{}"}
        assert "input_data" not in call
        assert "output_data" not in call

    def test_only_returns_tool_calls_for_the_given_run(self, api_client):
        agent_run_a = AgentRunFactory()
        agent_run_b = AgentRunFactory()
        ToolCallFactory(agent_run=agent_run_a)
        ToolCallFactory(agent_run=agent_run_b)

        response = api_client.get(f"/api/agent-runs/{agent_run_a.id}/tool-calls/")

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_no_tool_calls_returns_empty_list(self, api_client):
        agent_run = AgentRunFactory()

        response = api_client.get(f"/api/agent-runs/{agent_run.id}/tool-calls/")

        assert response.status_code == 200
        assert response.data == []

    def test_nonexistent_agent_run_returns_404(self, api_client):
        response = api_client.get(
            "/api/agent-runs/00000000-0000-0000-0000-000000000000/tool-calls/"
        )

        assert response.status_code == 404

    def test_tool_calls_query_count_optimized(
        self, api_client, django_assert_num_queries
    ):
        agent_run = AgentRunFactory()
        for i in range(5):
            ToolCallFactory(
                agent_run=agent_run,
                tool_name=f"tool_{i}",
                input_data={"idx": i},
                output_data={"result": i},
            )

        # 2 queries: 1 for agent_run get_object with select_related,
        # 1 for tool_calls list with select_related
        with django_assert_num_queries(2):
            response = api_client.get(f"/api/agent-runs/{agent_run.id}/tool-calls/")
            assert response.status_code == 200
            assert len(response.data) == 5
