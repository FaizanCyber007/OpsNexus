import pytest

from orchestration.model_client import LLMConfigurationError, LLMFactory


class TestGetSupervisorLlm:
    def test_raises_configuration_error_when_key_missing(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        with pytest.raises(LLMConfigurationError, match="GOOGLE_API_KEY"):
            LLMFactory().get_supervisor_llm()

    def test_returns_client_when_key_present(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "fake-key-for-test")

        llm = LLMFactory().get_supervisor_llm()

        assert llm is not None


class TestGetWorkerLlm:
    def test_raises_configuration_error_when_key_missing(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        with pytest.raises(LLMConfigurationError, match="GROQ_API_KEY"):
            LLMFactory().get_worker_llm()

    def test_returns_client_when_key_present(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-test")

        llm = LLMFactory().get_worker_llm()

        assert llm is not None
