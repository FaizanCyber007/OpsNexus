"""Model-client factory for the Supervisor/Worker LLM split.

`get_supervisor_llm()` returns a Gemini client (classification/orchestration
reasoning) and `get_worker_llm()` returns a Groq-hosted client (fast,
high-volume tool-calling) -- see the model-selection rationale in the root
README. Both API keys are read from the environment (never hardcoded); if a
key is missing, the getter raises `LLMConfigurationError` with an actionable
message instead of crashing at import time, so callers can catch it and fall
back to the deterministic mock pipeline.
"""

import os


class LLMConfigurationError(RuntimeError):
    """Raised when a required LLM provider API key is not configured."""


# gemini-1.5-flash / llama3-70b-8192 / llama-3.3-70b-versatile have each been
# retired by their providers in turn; these are the current equivalents in
# the same tier (fast supervisor / large tool-calling-capable worker),
# reconfirmed against each provider's live model list each time.
SUPERVISOR_MODEL_NAME = "gemini-2.5-flash"
WORKER_MODEL_NAME = "openai/gpt-oss-120b"


class LLMFactory:
    """Centralized point for obtaining the LLM client each agent role uses."""

    def get_supervisor_llm(self):
        """Return a configured Gemini client for Supervisor classification."""
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise LLMConfigurationError(
                "GOOGLE_API_KEY is not set in backend/.env -- the Gemini "
                "Supervisor cannot run without it."
            )

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=SUPERVISOR_MODEL_NAME,
            google_api_key=api_key,
            temperature=0,
        )

    def get_worker_llm(self):
        """Return a configured Groq client for Worker tool-calling."""
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise LLMConfigurationError(
                "GROQ_API_KEY is not set in backend/.env -- the Groq Worker "
                "cannot run without it."
            )

        from langchain_groq import ChatGroq

        return ChatGroq(
            model=WORKER_MODEL_NAME,
            groq_api_key=api_key,
            temperature=0,
        )
