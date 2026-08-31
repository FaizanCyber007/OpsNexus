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
from memory.vector_client import extract_text_from_fieldfile
from orchestration.graph import ComplianceWorkerError, InvoiceWorkerError, SalesWorkerError, graph
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


# Maximum time (seconds) allowed for the LangGraph graph execution.
# Prevents the RQ worker from blocking indefinitely when an LLM call
# or MCP connection hangs.
GRAPH_EXECUTION_TIMEOUT_SECONDS = 120


async def trigger_agent_run(document_id) -> None:
    document = await Document.objects.aget(id=document_id)

    # Mark the document as actively processing so the frontend knows
    # progress is happening (not stuck in "pending").
    document.status = Document.Status.PROCESSING
    await document.asave(update_fields=["status"])

    document_text = ""
    if document.file:
        document_text = await asyncio.to_thread(
            extract_text_from_fieldfile, document.file
        )

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
        result = await asyncio.wait_for(
            graph.ainvoke(
                {
                    "organization_id": str(document.organization_id),
                    "document_text": document_text,
                    "route": "",
                    "reasoning": "",
                    "answer": None,
                    "compliance_audit": None,
                    "invoice_reconciliation": None,
                    "worker_tool_calls": [],
                }
            ),
            timeout=GRAPH_EXECUTION_TIMEOUT_SECONDS,
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
    except ComplianceWorkerError as exc:
        logger.error("Compliance Worker failed for document %s: %s", document_id, exc)
        agent_run.status = AgentRun.Status.FAILED
        agent_run.error_message = f"Compliance Worker failed: {exc}"
        agent_run.finished_at = timezone.now()
        await agent_run.asave()

        document.status = Document.Status.FAILED
        await document.asave()
        return
    except InvoiceWorkerError as exc:
        logger.error("Invoice Worker failed for document %s: %s", document_id, exc)
        agent_run.status = AgentRun.Status.FAILED
        agent_run.error_message = f"Invoice Worker failed: {exc}"
        agent_run.finished_at = timezone.now()
        await agent_run.asave()

        document.status = Document.Status.FAILED
        await document.asave()
        return
    except asyncio.TimeoutError:
        logger.error(
            "Graph execution timed out after %ds for document %s; "
            "falling back to mock pipeline.",
            GRAPH_EXECUTION_TIMEOUT_SECONDS,
            document_id,
        )
        agent_run.status = AgentRun.Status.FAILED
        agent_run.error_message = (
            f"Agent pipeline timed out after {GRAPH_EXECUTION_TIMEOUT_SECONDS}s. "
            "One or more LLM or MCP calls did not respond in time."
        )
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

    if route == "compliance_audit" and result.get("compliance_audit") is not None:
        for call in result.get("worker_tool_calls", []):
            await ToolCall.objects.acreate(
                agent_run=agent_run,
                tool_name=call["tool_name"],
                input_data=call["input"],
                output_data={"result": call["output"]},
            )

        audit = result["compliance_audit"]
        compliance_status = "COMPLIANT" if audit.is_compliant else "NON-COMPLIANT"

        violations_block = (
            "\n".join(f"  • {v}" for v in audit.violations)
            if audit.violations
            else "  None found."
        )
        remediations_block = (
            "\n".join(f"  {i + 1}. {r}" for i, r in enumerate(audit.recommended_remediations))
            if audit.recommended_remediations
            else "  No remediations required."
        )

        content = (
            f"Compliance Audit Result: {compliance_status}\n"
            f"Severity: {audit.severity}\n\n"
            f"Violations Found ({len(audit.violations)}):\n{violations_block}\n\n"
            f"Recommended Remediations:\n{remediations_block}"
        )
        executive_summary = (
            f"Document is {compliance_status} with {len(audit.violations)} violation(s) "
            f"at {audit.severity} severity."
        )

        await Answer.objects.acreate(
            agent_run=agent_run,
            question_text="Audit this document for security policy compliance.",
            content=content,
            executive_summary=executive_summary,
            risk_flags=audit.violations,
            action_items=audit.recommended_remediations,
            confidence_score=None,
            is_verified=False,
        )
        agent_run.status = AgentRun.Status.SUCCEEDED
        agent_run.finished_at = timezone.now()
        await agent_run.asave()

        document.status = Document.Status.COMPLETED
        await document.asave()

        logger.info(
            "Compliance Worker resolved document %s (route=%s, compliant=%s, severity=%s)",
            document_id,
            route,
            audit.is_compliant,
            audit.severity,
        )
        return

    if route == "invoice_reconciliation" and result.get("invoice_reconciliation") is not None:
        for call in result.get("worker_tool_calls", []):
            await ToolCall.objects.acreate(
                agent_run=agent_run,
                tool_name=call["tool_name"],
                input_data=call["input"],
                output_data={"result": call["output"]},
            )

        reconciliation = result["invoice_reconciliation"]
        payment_status = "APPROVED FOR PAYMENT" if reconciliation.approved_for_payment else "PENDING REVIEW"
        match_status = "MATCHED" if reconciliation.is_matched else "DISCREPANCIES FOUND"

        discrepancies_block = (
            "\n".join(f"  • {d}" for d in reconciliation.discrepancies)
            if reconciliation.discrepancies
            else "  None — invoice reconciles perfectly with the purchase order ledger."
        )
        action_items = (
            [f"Resolve discrepancy: {d}" for d in reconciliation.discrepancies]
            if reconciliation.discrepancies
            else ["Proceed with payment processing — invoice is fully reconciled."]
        )

        content = (
            f"Invoice Reconciliation Result: {match_status}\n"
            f"Payment Status: {payment_status}\n"
            f"Extracted Invoice Total: ${reconciliation.extracted_total:,.2f}\n\n"
            f"Discrepancies Found ({len(reconciliation.discrepancies)}):\n"
            f"{discrepancies_block}"
        )
        executive_summary = (
            f"Invoice {match_status.lower()} with {len(reconciliation.discrepancies)} "
            f"discrepancy(ies). Extracted total: ${reconciliation.extracted_total:,.2f}. "
            f"Status: {payment_status}."
        )

        await Answer.objects.acreate(
            agent_run=agent_run,
            question_text="Reconcile this invoice against the internal purchase order ledger.",
            content=content,
            executive_summary=executive_summary,
            risk_flags=reconciliation.discrepancies,
            action_items=action_items,
            confidence_score=None,
            is_verified=False,
        )
        agent_run.status = AgentRun.Status.SUCCEEDED
        agent_run.finished_at = timezone.now()
        await agent_run.asave()

        document.status = Document.Status.COMPLETED
        await document.asave()

        logger.info(
            "Invoice Worker resolved document %s (route=%s, matched=%s, approved=%s, total=%.2f)",
            document_id,
            route,
            reconciliation.is_matched,
            reconciliation.approved_for_payment,
            reconciliation.extracted_total,
        )
        return

    # Fall back to mock resolution for any route that did not produce a dedicated result
    agent_run.status = AgentRun.Status.SUCCEEDED
    agent_run.finished_at = timezone.now()
    await agent_run.asave()

    logger.info(
        "Document %s classified as '%s'; falling back to mock resolution",
        document_id,
        route,
    )
    await trigger_mock_agent_run(document_id)
    return
