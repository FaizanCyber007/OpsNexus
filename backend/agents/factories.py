import factory
from factory.django import DjangoModelFactory

from documents.factories import DocumentFactory

from .models import AgentProfile, AgentRun, Answer, ToolCall


class AgentProfileFactory(DjangoModelFactory):
    class Meta:
        model = AgentProfile

    name = factory.Sequence(lambda n: f"Test Agent {n}")
    system_prompt = "You are a test agent."
    model_name = "test-model"
    temperature = 0.0


class AgentRunFactory(DjangoModelFactory):
    class Meta:
        model = AgentRun

    document = factory.SubFactory(DocumentFactory)
    agent_profile = factory.SubFactory(AgentProfileFactory)
    status = AgentRun.Status.SUCCEEDED


class ToolCallFactory(DjangoModelFactory):
    class Meta:
        model = ToolCall

    agent_run = factory.SubFactory(AgentRunFactory)
    tool_name = "test_tool"
    input_data = factory.LazyFunction(dict)
    output_data = factory.LazyFunction(dict)


class AnswerFactory(DjangoModelFactory):
    class Meta:
        model = Answer

    agent_run = factory.SubFactory(AgentRunFactory)
    content = "Test answer content."
    confidence_score = 0.9
    is_verified = False
