"""Real entry point for document resolution, replacing the mock trigger.

Classifies the document via the Gemini Supervisor and, for `sales_rfp`, runs
the real Groq Sales Worker. Any other route -- or any failure, including
missing API keys -- falls back to `orchestration.runner.trigger_mock_agent_run`
so the pipeline always completes.
"""

import asyncio
import logging

from django.utils import timezone

from agents.models import AgentProfile, AgentRun, Answer, ToolCall
from documents.models import Document
from memory.vector_client import extract_text
from orchestration.graph import SalesWorkerError, graph
from orchestration.model_client import (
    SUPERVISOR_MODEL_NAME,
    WORKER_MODEL_NAME,
    LLMConfigurationError,
)
from orchestration.runner import trigger_mock_agent_run

logger = logging.getLogger(__name__)

AGENT_PROFILE_NAME = "OpsNexus Supervisor/Worker Swarm"
AGENT_PROFILE_DEFAULTS = {
    "system_prompt": (
        "Gemini Supervisor classifies the document; for sales_rfp, a Groq "
        "Worker drafts a response using the search_company_knowledge tool."
    ),
    "model_name": f"{SUPERVISOR_MODEL_NAME}+{WORKER_MODEL_NAME}",
    "temperature": 0.0,
}


async def trigger_agent_run(document_id) -> None:
    document = await Document.objects.aget(id=document_id)

    document_text = ""
    if document.file:
        document_text = await asyncio.to_thread(extract_text, document.file.path)

    agent_profile, _ = await AgentProfile.objects.aget_or_create(
        name=AGENT_PROFILE_NAME,
        defaults=AGENT_PROFILE_DEFAULTS,
    )

    agent_run = await AgentRun.objects.acreate(
        document=document,
        agent_profile=agent_profile,
        status=AgentRun.Status.RUNNING,
        started_at=timezone.now(),
    )

    try:
        result = await graph.ainvoke(
            {
                "organization_id": str(document.organization_id),
                "document_text": document_text,
                "route": "",
                "reasoning": "",
                "answer": None,
                "worker_tool_calls": [],
            }
        )
    except SalesWorkerError as exc:
        logger.error("Sales Worker failed for document %s: %s", document_id, exc)
        agent_run.status = AgentRun.Status.FAILED
        agent_run.error_message = f"Sales Worker failed: {exc}"
        agent_run.finished_at = timezone.now()
        await agent_run.asave()

        document.status = Document.Status.FAILED
        await document.asave()
        return
    except LLMConfigurationError as exc:
        logger.warning(
            "LLM not configured (%s); falling back to mock for document %s",
            exc,
            document_id,
        )
        agent_run.status = AgentRun.Status.FAILED
        agent_run.error_message = str(exc)
        agent_run.finished_at = timezone.now()
        await agent_run.asave()
        await trigger_mock_agent_run(document_id)
        return
    except Exception:
        logger.exception("LangGraph agent run failed for document %s", document_id)
        agent_run.status = AgentRun.Status.FAILED
        agent_run.error_message = "LangGraph agent run raised an unexpected error"
        agent_run.finished_at = timezone.now()
        await agent_run.asave()
        await trigger_mock_agent_run(document_id)
        return

    route = result["route"]
    await ToolCall.objects.acreate(
        agent_run=agent_run,
        tool_name="langgraph_supervisor_classify",
        input_data={"document_id": str(document_id)},
        output_data={"route": route, "reasoning": result.get("reasoning", "")},
    )

    if route == "sales_rfp" and result.get("answer") is not None:
        for call in result.get("worker_tool_calls", []):
            await ToolCall.objects.acreate(
                agent_run=agent_run,
                tool_name=call["tool_name"],
                input_data=call["input"],
                output_data={"result": call["output"]},
            )

        answer = result["answer"]
        await Answer.objects.acreate(
            agent_run=agent_run,
            question_text="Draft a response to this RFP/questionnaire.",
            content=answer.content,
            executive_summary=answer.executive_summary,
            risk_flags=answer.risk_flags,
            action_items=answer.action_items,
            confidence_score=answer.confidence_score,
            is_verified=False,
        )
        agent_run.status = AgentRun.Status.SUCCEEDED
        agent_run.finished_at = timezone.now()
        await agent_run.asave()

        document.status = Document.Status.COMPLETED
        await document.asave()

        logger.info("Sales Worker resolved document %s (route=%s)", document_id, route)
        return

    agent_run.status = AgentRun.Status.SUCCEEDED
    agent_run.finished_at = timezone.now()
    await agent_run.asave()

    logger.info(
        "Document %s classified as '%s'; falling back to mock resolution "
        "(no real Worker for this route yet)",
        document_id,
        route,
    )
    await trigger_mock_agent_run(document_id)
