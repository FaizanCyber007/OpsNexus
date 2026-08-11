import asyncio
import logging

from django.utils import timezone

from agents.models import AgentProfile, AgentRun, Answer, ToolCall
from documents.models import Document
from orchestration.router import DeterministicRouter

logger = logging.getLogger(__name__)

MOCK_AGENT_PROFILE_NAME = "Mock Agent"
MOCK_AGENT_PROFILE_DEFAULTS = {
    "system_prompt": "You are a mock OpsNexus sub-agent used for local development.",
    "model_name": "mock-model",
    "temperature": 0.0,
}


async def trigger_mock_agent_run(document_id) -> None:
    """Stub of the future async agent execution pipeline.

    Simulates processing latency, then writes a mock AgentRun/ToolCall/Answer
    trail and marks the document completed -- to be replaced by a real
    Claude-driven agent loop.
    """
    await asyncio.sleep(2)

    document = await Document.objects.aget(id=document_id)
    route = DeterministicRouter().route(document)

    agent_profile, _ = await AgentProfile.objects.aget_or_create(
        name=MOCK_AGENT_PROFILE_NAME,
        defaults=MOCK_AGENT_PROFILE_DEFAULTS,
    )

    agent_run = await AgentRun.objects.acreate(
        document=document,
        agent_profile=agent_profile,
        status=AgentRun.Status.RUNNING,
        started_at=timezone.now(),
    )

    await ToolCall.objects.acreate(
        agent_run=agent_run,
        tool_name="mock_classifier",
        input_data={"file_path": document.file_path, "route": route},
        output_data={"route": route, "result": "mock_success"},
    )

    await Answer.objects.acreate(
        agent_run=agent_run,
        content=f"Mock resolution generated via route '{route}'.",
        confidence_score=1.0,
        is_verified=False,
    )

    agent_run.status = AgentRun.Status.SUCCEEDED
    agent_run.finished_at = timezone.now()
    await agent_run.asave()

    document.status = Document.Status.COMPLETED
    await document.asave()

    logger.info(
        "Mock agent run completed for document %s via route '%s'",
        document_id,
        route,
    )
