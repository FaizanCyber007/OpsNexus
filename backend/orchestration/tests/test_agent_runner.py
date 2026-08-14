import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.models import AgentRun, Answer
from documents.factories import DocumentFactory
from documents.models import Document
from orchestration.agent_runner import trigger_agent_run
from orchestration.graph import SalesWorkerError, StructuredAnswer
from orchestration.model_client import LLMConfigurationError


@pytest.mark.django_db(transaction=True)
class TestTriggerAgentRun:
    def test_sales_worker_error_marks_document_and_run_failed(self):
        document = DocumentFactory()

        with (
            patch(
                "orchestration.agent_runner.graph.ainvoke",
                AsyncMock(side_effect=SalesWorkerError("groq timed out")),
            ),
            patch(
                "orchestration.agent_runner.trigger_mock_agent_run",
                AsyncMock(),
            ) as mock_fallback,
        ):
            asyncio.run(trigger_agent_run(document.id))

        document.refresh_from_db()
        assert document.status == Document.Status.FAILED
        mock_fallback.assert_not_called()

        run = AgentRun.objects.get(document=document)
        assert run.status == AgentRun.Status.FAILED
        assert "groq timed out" in run.error_message

    def test_missing_api_key_falls_back_to_mock(self):
        document = DocumentFactory()

        with (
            patch(
                "orchestration.agent_runner.graph.ainvoke",
                AsyncMock(
                    side_effect=LLMConfigurationError("GOOGLE_API_KEY is not set")
                ),
            ),
            patch(
                "orchestration.agent_runner.trigger_mock_agent_run",
                AsyncMock(),
            ) as mock_fallback,
        ):
            asyncio.run(trigger_agent_run(document.id))

        mock_fallback.assert_awaited_once_with(document.id)

        run = AgentRun.objects.get(document=document)
        assert run.status == AgentRun.Status.FAILED
        assert "GOOGLE_API_KEY" in run.error_message

    def test_unexpected_error_falls_back_to_mock(self):
        document = DocumentFactory()

        with (
            patch(
                "orchestration.agent_runner.graph.ainvoke",
                AsyncMock(side_effect=RuntimeError("something broke")),
            ),
            patch(
                "orchestration.agent_runner.trigger_mock_agent_run",
                AsyncMock(),
            ) as mock_fallback,
        ):
            asyncio.run(trigger_agent_run(document.id))

        mock_fallback.assert_awaited_once_with(document.id)

    def test_successful_sales_rfp_creates_answer_and_completes_document(self):
        document = DocumentFactory()
        answer = StructuredAnswer(
            content="Here is our RFP response.", confidence_score=0.9
        )

        with (
            patch(
                "orchestration.agent_runner.graph.ainvoke",
                AsyncMock(
                    return_value={
                        "route": "sales_rfp",
                        "reasoning": "It's an RFP.",
                        "answer": answer,
                    }
                ),
            ),
            patch(
                "orchestration.agent_runner.trigger_mock_agent_run",
                AsyncMock(),
            ) as mock_fallback,
        ):
            asyncio.run(trigger_agent_run(document.id))

        mock_fallback.assert_not_called()

        document.refresh_from_db()
        assert document.status == Document.Status.COMPLETED

        run = AgentRun.objects.get(document=document)
        assert run.status == AgentRun.Status.SUCCEEDED

        saved_answer = Answer.objects.get(agent_run=run)
        assert saved_answer.content == "Here is our RFP response."
        assert saved_answer.confidence_score == 0.9

    def test_non_sales_rfp_route_falls_back_to_mock_without_creating_answer(self):
        document = DocumentFactory()

        with (
            patch(
                "orchestration.agent_runner.graph.ainvoke",
                AsyncMock(
                    return_value={
                        "route": "invoice_reconciliation",
                        "reasoning": "It's an invoice.",
                        "answer": None,
                    }
                ),
            ),
            patch(
                "orchestration.agent_runner.trigger_mock_agent_run",
                AsyncMock(),
            ) as mock_fallback,
        ):
            asyncio.run(trigger_agent_run(document.id))

        mock_fallback.assert_awaited_once_with(document.id)

        run = AgentRun.objects.get(document=document)
        assert run.status == AgentRun.Status.SUCCEEDED
        assert not Answer.objects.filter(agent_run=run).exists()
