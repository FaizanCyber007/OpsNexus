"""Model-client factory for the Supervisor/Worker LLM split.

`get_supervisor_llm()` returns a Gemini client (classification/orchestration
reasoning) and `get_worker_llm()` returns a Groq-hosted client (fast,
high-volume tool-calling) -- see the model-selection rationale in the root
README. Both API keys are read from the environment (never hardcoded); if a
key is missing, the getter raises `LLMConfigurationError` with an actionable
message instead of crashing at import time, so callers can catch it and fall
back to the deterministic mock pipeline.

## Retry & Fallback Guardrails

Every LLM client returned by this factory is hardened with:

1. **Tenacity exponential-backoff retries** (max 3 attempts, 2–10 s wait)
   catching `groq.RateLimitError` and `groq.APIStatusError` (covers
   503 ServiceUnavailable).  The policy is applied via LangChain's native
   `Runnable.with_retry()`, which preserves `.with_structured_output()`,
   `.bind_tools()`, and all other ``Runnable`` capabilities -- no monkey-
   patching is needed and the approach is fully compatible with Pydantic v2.

2. **Provider fallback** on the Worker chain: if Groq exhausts all retries,
   LangChain's `.with_fallbacks([gemini_llm])` seamlessly routes the call to
   the Gemini model so the pipeline never hard-crashes due to a Groq outage.
"""

import logging
import os


logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Public constants (imported by agent_runner.py and tests)
# ------------------------------------------------------------------

# gemini-1.5-flash / llama3-70b-8192 / llama-3.3-70b-versatile have each been
# retired by their providers in turn; these are the current equivalents in
# the same tier (fast supervisor / large tool-calling-capable worker),
# reconfirmed against each provider's live model list each time.
SUPERVISOR_MODEL_NAME = "gemini-2.5-flash"
WORKER_MODEL_NAME = "openai/gpt-oss-120b"

# How many total attempts are made on transient API errors (1 original + N-1 retries).
LLM_RETRY_ATTEMPTS = 3


# ------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------


class LLMConfigurationError(RuntimeError):
    """Raised when a required LLM provider API key is not configured."""


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _get_retryable_exceptions():
    """Return the tuple of transient exceptions tenacity should retry on.

    Imported lazily so that the absence of the `groq` package at import time
    does not break the module for non-Groq code paths.
    """
    try:
        import groq

        return (groq.RateLimitError, groq.APIStatusError)
    except ImportError:  # pragma: no cover
        # groq is always present in our virtualenv; guard for safety only.
        return (OSError,)


def _apply_retry_policy(llm):
    """Return *llm* wrapped with LangChain's native ``with_retry()`` policy.

    ``with_retry()`` is available on every ``Runnable`` subclass and is the
    idiomatic way to attach tenacity retries in LangChain without breaking
    Pydantic v2's strict ``__setattr__``.

    Retry policy:
    - Retries on: ``groq.RateLimitError``, ``groq.APIStatusError`` (503)
    - Max attempts: ``LLM_RETRY_ATTEMPTS`` (3)
    - Wait: exponential backoff (min 2 s, max 10 s)
    - Reraises the last exception if all attempts fail
    """
    return llm.with_retry(
        retry_if_exception_type=_get_retryable_exceptions(),
        stop_after_attempt=LLM_RETRY_ATTEMPTS,
        wait_exponential_jitter=True,
        exponential_jitter_params={"initial": 2.0, "max": 10.0},
    )


# ------------------------------------------------------------------
# Public factory
# ------------------------------------------------------------------


class LLMFactory:
    """Centralized point for obtaining the LLM client each agent role uses."""

    @staticmethod
    def apply_retry_policy(runnable):
        """Public helper to wrap any Runnable with the project's standard retry policy."""
        return _apply_retry_policy(runnable)

    def get_supervisor_llm(self):
        """Return a configured Gemini client for Supervisor classification.

        The returned Runnable wraps ``ChatGoogleGenerativeAI`` with the
        standard tenacity retry policy (see module docstring). Callers may
        still chain ``.with_structured_output()`` on the result because
        ``with_retry()`` preserves all Runnable method bindings.
        """
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise LLMConfigurationError(
                "GOOGLE_API_KEY is not set in backend/.env -- the Gemini "
                "Supervisor cannot run without it."
            )

        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model=SUPERVISOR_MODEL_NAME,
            google_api_key=api_key,
            temperature=0,
        )
        return _apply_retry_policy(llm)

    def get_worker_llm(self):
        """Return a Groq-primary / Gemini-fallback worker chain.

        Architecture:
        - Primary: Groq (fast, cheap tool-calling), with tenacity retries.
        - Fallback: Gemini (same key as Supervisor; activated automatically
          by LangChain's ``.with_fallbacks()`` if Groq raises on all retry
          attempts).

        The resulting chain is returned as-is; callers use it exactly like a
        plain ``ChatGroq`` instance (``create_react_agent``, ``ainvoke``, etc).
        """
        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            raise LLMConfigurationError(
                "GROQ_API_KEY is not set in backend/.env -- the Groq Worker "
                "cannot run without it."
            )

        from langchain_groq import ChatGroq

        groq_llm = _apply_retry_policy(
            ChatGroq(
                model=WORKER_MODEL_NAME,
                groq_api_key=groq_key,
                temperature=0,
            )
        )

        # Build the Gemini fallback only when its key is available; if not,
        # we still return Groq-only (the LLMConfigurationError for Groq is
        # the priority signal, not the absence of the optional fallback key).
        google_key = os.environ.get("GOOGLE_API_KEY")
        if google_key:
            from langchain_google_genai import ChatGoogleGenerativeAI

            gemini_fallback = _apply_retry_policy(
                ChatGoogleGenerativeAI(
                    model=SUPERVISOR_MODEL_NAME,
                    google_api_key=google_key,
                    temperature=0,
                )
            )
            logger.debug("Worker LLM: Groq primary with Gemini fallback configured.")
            return groq_llm.with_fallbacks([gemini_fallback])

        logger.warning(
            "GOOGLE_API_KEY not set; Worker LLM has no provider fallback. "
            "A Groq outage will surface as a SalesWorkerError."
        )
        return groq_llm
