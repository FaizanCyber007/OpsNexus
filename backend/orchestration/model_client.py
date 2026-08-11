"""Stubbed model-client factory for the future Supervisor/Worker LLM split.

Week 6 will make this return real clients: `get_supervisor_llm()` backed by
Gemini (classification/orchestration reasoning) and `get_worker_llm()`
backed by Groq-hosted models (fast, high-volume tool-calling) -- see the
model-selection rationale in the root README. No `google-generativeai` or
`groq` dependency is installed yet; everything here is a mock config
object, not a live client.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MockLLMHandle:
    """Placeholder standing in for a real provider client instance."""

    provider: str
    model_name: str


class LLMFactory:
    """Centralized point for obtaining the LLM client each agent role uses."""

    def get_supervisor_llm(self) -> MockLLMHandle:
        """Week 6: return a configured Gemini client for Supervisor reasoning."""
        return MockLLMHandle(provider="gemini", model_name="gemini-mock")

    def get_worker_llm(self) -> MockLLMHandle:
        """Week 6: return a configured Groq client for Worker tool-calling."""
        return MockLLMHandle(provider="groq", model_name="groq-mock")
