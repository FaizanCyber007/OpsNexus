from unittest.mock import patch

import pytest

from orchestration.tool_registry import (
    ToolRegistry,
    build_search_company_knowledge_tool,
)


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        registry.register("my_tool", "a-tool-object")

        assert registry.get("my_tool") == "a-tool-object"

    def test_get_missing_tool_raises_key_error(self):
        registry = ToolRegistry()

        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_all_returns_a_copy(self):
        registry = ToolRegistry()
        registry.register("a", 1)

        snapshot = registry.all()
        snapshot["b"] = 2

        assert registry.all() == {"a": 1}


class TestSearchCompanyKnowledgeTool:
    def test_formats_results_from_chroma(self):
        fake_results = [
            {
                "text": "Prior answer about pricing.",
                "metadata": {"file_name": "rfp1.txt"},
            },
            {"text": "Prior answer about SLAs.", "metadata": {"file_name": "rfp2.txt"}},
        ]

        with patch("memory.vector_client.ChromaDBClient") as MockClient:
            MockClient.return_value.semantic_search.return_value = fake_results

            tool = build_search_company_knowledge_tool("org-123")
            output = tool.invoke({"query": "pricing"})

        MockClient.assert_called_once_with(collection_name="org_org-123")
        assert "[rfp1.txt] Prior answer about pricing." in output
        assert "[rfp2.txt] Prior answer about SLAs." in output

    def test_no_results_returns_placeholder_message(self):
        with patch("memory.vector_client.ChromaDBClient") as MockClient:
            MockClient.return_value.semantic_search.return_value = []

            tool = build_search_company_knowledge_tool("org-123")
            output = tool.invoke({"query": "pricing"})

        assert output == "No relevant prior context found."

    def test_missing_metadata_falls_back_to_unknown(self):
        with patch("memory.vector_client.ChromaDBClient") as MockClient:
            MockClient.return_value.semantic_search.return_value = [
                {"text": "some text", "metadata": {}}
            ]

            tool = build_search_company_knowledge_tool("org-123")
            output = tool.invoke({"query": "pricing"})

        assert "[unknown] some text" in output
