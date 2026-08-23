import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.models import AgentRun, Answer, ToolCall
from documents.factories import DocumentFactory
from documents.models import Document
from orchestration.runner import trigger_mock_agent_run


@pytest.mark.django_db(transaction=True)
class TestTriggerMockAgentRun:
    def test_creates_full_trail_and_completes_document(self):
        document = DocumentFactory(file_path="rfp_response.docx")

        with patch("orchestration.runner.asyncio.sleep", AsyncMock()):
            asyncio.run(trigger_mock_agent_run(document.id))

        document.refresh_from_db()
        assert document.status == Document.Status.COMPLETED

        run = AgentRun.objects.get(document=document)
        assert run.status == AgentRun.Status.SUCCEEDED
        assert run.agent_profile.name == "Mock Agent"

        tool_call = ToolCall.objects.get(agent_run=run)
        assert tool_call.tool_name == "mock_classifier"
        assert tool_call.output_data["route"] == "sales_rfp"

        answer = Answer.objects.get(agent_run=run)
        assert "sales_rfp" in answer.content
        assert answer.confidence_score == 1.0

    def test_route_reflects_deterministic_router(self):
        document = DocumentFactory(file_path="q3_invoice.pdf")

        with patch("orchestration.runner.asyncio.sleep", AsyncMock()):
            asyncio.run(trigger_mock_agent_run(document.id))

        run = AgentRun.objects.get(document=document)
        answer = Answer.objects.get(agent_run=run)
        assert "invoice_reconciliation" in answer.content

    def test_reuses_existing_mock_agent_profile(self):
        first = DocumentFactory(file_path="a.pdf")
        second = DocumentFactory(file_path="b.pdf")

        with patch("orchestration.runner.asyncio.sleep", AsyncMock()):
            asyncio.run(trigger_mock_agent_run(first.id))
            asyncio.run(trigger_mock_agent_run(second.id))

        profiles = {
            run.agent_profile_id
            for run in AgentRun.objects.filter(document__in=[first, second])
        }
        assert len(profiles) == 1
