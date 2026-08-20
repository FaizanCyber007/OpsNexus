"""Tests for the three production guardrails added in the refactor:

1. Pydantic auto-correction loop — supervisor retries on ValidationError and
   passes the error back to the LLM as a HumanMessage.
2. Tenacity retry logic — LLM calls are retried on transient API errors
   (RateLimitError / ServiceUnavailable) before failing.
3. Provider fallback — if Groq exhausts all retries, the worker chain
   transparently routes to the Gemini fallback.

Each test class is focused on *one* guardrail only; existing behaviour (happy
path, MCP fall-through, etc.) is covered in test_graph_nodes.py and
test_model_client.py.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage
from pydantic import ValidationError

from orchestration.graph import (
    MAX_VALIDATION_LOOPS,
    _run_sales_worker_agent,
    supervisor_node,
)
from orchestration.model_client import LLM_RETRY_ATTEMPTS, _apply_retry_policy
from orchestration.schemas import ClassificationResult, StructuredAnswer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_structured_answer(**overrides):
    defaults = dict(
        content="answer",
        executive_summary="summary",
        risk_flags=["Missing SOC2 Policy"],
        action_items=["Email CFO"],
        confidence_score=0.8,
    )
    defaults.update(overrides)
    return StructuredAnswer(**defaults)


def _make_validation_error():
    """Return a real pydantic ValidationError for testing.

    We deliberately construct one by passing an invalid value so it carries
    a real human-readable message that the correction prompt will embed.
    """
    try:
        ClassificationResult(route="invalid_route", reasoning="x")
    except ValidationError as exc:
        return exc
    raise AssertionError("Expected ValidationError was not raised")  # pragma: no cover


# ---------------------------------------------------------------------------
# 1. Pydantic Auto-Correction Loop
# ---------------------------------------------------------------------------


class TestPydanticAutoCorrectionLoop:
    """The supervisor must retry on ValidationError and feed the error back
    to the LLM before eventually either succeeding or propagating the error.
    """

    def test_supervisor_retries_on_validation_error_then_succeeds(self):
        """When the LLM raises ValidationError once then returns a valid result,
        ``supervisor_node`` must:
          - Call the LLM *twice* (one failure + one corrected call).
          - Include a HumanMessage containing the validation error text on the
            second call.
          - Return the successful classification.
        """
        validation_err = _make_validation_error()
        good_result = ClassificationResult(
            route="sales_rfp", reasoning="Mentions RFP and SOC2."
        )

        # ainvoke: first call raises, second call succeeds.
        fake_llm = MagicMock()
        fake_llm.with_structured_output.return_value.ainvoke = AsyncMock(
            side_effect=[validation_err, good_result]
        )

        with patch("orchestration.graph.LLMFactory") as MockFactory:
            MockFactory.return_value.get_supervisor_llm.return_value = fake_llm

            result = asyncio.run(
                supervisor_node({"document_text": "Please respond to this RFP."})
            )

        assert result == {"route": "sales_rfp", "reasoning": "Mentions RFP and SOC2."}

        mock_ainvoke = fake_llm.with_structured_output.return_value.ainvoke
        assert mock_ainvoke.call_count == 2, (
            f"Expected 2 LLM calls (1 fail + 1 correction), got "
            f"{mock_ainvoke.call_count}"
        )

        # The second call's message list must contain a HumanMessage with the
        # validation error embedded.
        second_call_messages = mock_ainvoke.call_args_list[1].args[0]
        human_messages = [
            m for m in second_call_messages if isinstance(m, HumanMessage)
        ]
        assert human_messages, "No HumanMessage found in the correction call"
        correction_text = human_messages[-1].content
        assert "failed validation" in correction_text.lower(), (
            f"Correction prompt does not mention 'failed validation': "
            f"{correction_text!r}"
        )

    def test_supervisor_raises_after_max_validation_loops(self):
        """When the LLM *always* raises ValidationError, ``supervisor_node``
        must propagate it after exactly ``MAX_VALIDATION_LOOPS + 1`` total
        LLM calls (not swallow it, not loop forever).
        """
        validation_err = _make_validation_error()

        fake_llm = MagicMock()
        fake_llm.with_structured_output.return_value.ainvoke = AsyncMock(
            side_effect=validation_err
        )

        with patch("orchestration.graph.LLMFactory") as MockFactory:
            MockFactory.return_value.get_supervisor_llm.return_value = fake_llm

            with pytest.raises(ValidationError):
                asyncio.run(
                    supervisor_node({"document_text": "Some document with bad output."})
                )

        expected_calls = MAX_VALIDATION_LOOPS + 1
        actual_calls = fake_llm.with_structured_output.return_value.ainvoke.call_count
        assert actual_calls == expected_calls, (
            f"Expected exactly {expected_calls} LLM calls before giving up, "
            f"got {actual_calls}"
        )

    def test_sales_worker_retries_on_validation_error_then_succeeds(self):
        """``_run_sales_worker_agent`` must retry the ReAct agent on
        ValidationError, appending a correction HumanMessage to the message
        list before re-invoking.
        """
        validation_err = _make_validation_error()
        good_answer = _make_structured_answer(content="corrected answer")

        # The agent returns a good result on the second attempt.
        fake_agent = MagicMock()
        fake_agent.ainvoke = AsyncMock(
            side_effect=[
                validation_err,
                {
                    "structured_response": good_answer,
                    "messages": [],
                },
            ]
        )

        with patch("orchestration.graph.LLMFactory"), patch(
            "langgraph.prebuilt.create_react_agent", return_value=fake_agent
        ):
            answer, tool_calls = asyncio.run(
                _run_sales_worker_agent("some rfp text", tools=[])
            )

        assert answer == good_answer
        assert fake_agent.ainvoke.call_count == 2

        # Second call must carry a correction HumanMessage in its messages.
        second_call_input = fake_agent.ainvoke.call_args_list[1].args[0]
        messages_sent = second_call_input["messages"]
        human_corrections = [m for m in messages_sent if isinstance(m, HumanMessage)]
        assert human_corrections, "No HumanMessage correction found in second call"
        assert "failed validation" in human_corrections[-1].content.lower()


# ---------------------------------------------------------------------------
# 2. Tenacity Retry Logic
# ---------------------------------------------------------------------------


class TestTenacityRetry:
    """Prove that ``_apply_retry_policy`` wires tenacity retries correctly.

    We use ``with_retry()`` — LangChain's built-in Pydantic-safe retry
    mechanism — rather than monkey-patching.  The test verifies that
    ``_apply_retry_policy`` calls ``with_retry()`` on the LLM with the
    expected keyword arguments (attempt cap and exception filter).
    """

    def test_apply_retry_policy_calls_with_retry_with_correct_params(self, monkeypatch):
        """``_apply_retry_policy(llm)`` must invoke ``llm.with_retry()`` with:

        * ``stop_after_attempt = LLM_RETRY_ATTEMPTS``
        * ``retry_if_exception_type`` = a tuple containing at least
          ``groq.RateLimitError`` and ``groq.APIStatusError``
        """
        import groq

        mock_llm = MagicMock(name="RawLLM")
        retry_result = MagicMock(name="RetryWrapped")
        mock_llm.with_retry.return_value = retry_result

        result = _apply_retry_policy(mock_llm)

        mock_llm.with_retry.assert_called_once()
        call_kwargs = mock_llm.with_retry.call_args.kwargs

        assert call_kwargs["stop_after_attempt"] == LLM_RETRY_ATTEMPTS, (
            f"Expected stop_after_attempt={LLM_RETRY_ATTEMPTS}, "
            f"got {call_kwargs.get('stop_after_attempt')}"
        )
        retryable = call_kwargs["retry_if_exception_type"]
        assert (
            groq.RateLimitError in retryable
        ), "groq.RateLimitError must be in retry_if_exception_type"
        assert (
            groq.APIStatusError in retryable
        ), "groq.APIStatusError must be in retry_if_exception_type"
        # The return value is the with_retry() result, not the original LLM.
        assert result is retry_result

    def test_apply_retry_policy_returns_with_retry_runnable(self, monkeypatch):
        """The return value of ``_apply_retry_policy`` is the Runnable returned
        by ``llm.with_retry()``, not the original LLM instance."""
        mock_llm = MagicMock(name="RawLLM")
        wrapped = MagicMock(name="WithRetryRunnable")
        mock_llm.with_retry.return_value = wrapped

        result = _apply_retry_policy(mock_llm)

        assert (
            result is wrapped
        ), "Expected _apply_retry_policy to return with_retry() result"


# ---------------------------------------------------------------------------
# 3. Provider Fallback
# ---------------------------------------------------------------------------


class TestProviderFallback:
    """Prove the worker chain falls back from Groq to Gemini on failure."""

    def test_get_worker_llm_builds_fallback_chain_when_google_key_present(
        self, monkeypatch
    ):
        """``get_worker_llm()`` must call ``.with_fallbacks([gemini_with_retry])``
        when ``GOOGLE_API_KEY`` is available.

        ``_apply_retry_policy`` calls ``llm.with_retry()`` first, so the chain is:
            groq_with_retry.with_fallbacks([gemini_with_retry])
        """
        monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
        monkeypatch.setenv("GOOGLE_API_KEY", "fake-google-key")

        groq_mock = MagicMock(name="GroqLLM")
        groq_retry_mock = MagicMock(name="GroqWithRetry")
        groq_mock.with_retry.return_value = groq_retry_mock

        gemini_mock = MagicMock(name="GeminiLLM")
        gemini_retry_mock = MagicMock(name="GeminiWithRetry")
        gemini_mock.with_retry.return_value = gemini_retry_mock

        chain_mock = MagicMock(name="FallbackChain")
        groq_retry_mock.with_fallbacks.return_value = chain_mock

        with (
            patch("langchain_groq.ChatGroq", return_value=groq_mock),
            patch(
                "langchain_google_genai.ChatGoogleGenerativeAI",
                return_value=gemini_mock,
            ),
        ):
            from orchestration.model_client import LLMFactory as _LLMFactory

            result = _LLMFactory().get_worker_llm()

        # with_fallbacks must be called on the retry-wrapped Groq runnable.
        groq_retry_mock.with_fallbacks.assert_called_once()
        fallbacks_passed = groq_retry_mock.with_fallbacks.call_args.args[0]
        assert len(fallbacks_passed) == 1, "Expected exactly one fallback LLM"
        assert (
            fallbacks_passed[0] is gemini_retry_mock
        ), "Fallback must be the retry-wrapped Gemini, not the raw instance"
        assert result is chain_mock

    def test_get_worker_llm_returns_groq_only_without_google_key(self, monkeypatch):
        """Without ``GOOGLE_API_KEY``, no fallback is configured and the
        retry-wrapped Groq Runnable is returned directly.
        """
        monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        groq_mock = MagicMock(name="GroqLLM")
        groq_retry_mock = MagicMock(name="GroqWithRetry")
        groq_mock.with_retry.return_value = groq_retry_mock

        with patch("langchain_groq.ChatGroq", return_value=groq_mock):
            from orchestration.model_client import LLMFactory as _LLMFactory

            result = _LLMFactory().get_worker_llm()

        groq_retry_mock.with_fallbacks.assert_not_called()
        # Result is the retry-wrapped Groq (not the raw LLM instance).
        assert result is groq_retry_mock
