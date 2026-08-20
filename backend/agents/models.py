from django.db import models

from core.models import BaseModel
from documents.models import Document


class AgentProfile(BaseModel):
    name = models.CharField(max_length=255)
    system_prompt = models.TextField()
    model_name = models.CharField(max_length=255)
    temperature = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


class AgentRun(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="agent_runs",
    )
    agent_profile = models.ForeignKey(
        AgentProfile,
        on_delete=models.CASCADE,
        related_name="runs",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.agent_profile} -> {self.document} ({self.status})"


class ToolCall(BaseModel):
    agent_run = models.ForeignKey(
        AgentRun,
        on_delete=models.CASCADE,
        related_name="tool_calls",
    )
    tool_name = models.CharField(max_length=255)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.tool_name} ({self.agent_run_id})"


class Answer(BaseModel):
    agent_run = models.ForeignKey(
        AgentRun,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question_text = models.TextField(blank=True)
    content = models.TextField()
    confidence_score = models.FloatField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.content[:50]


class Citation(BaseModel):
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="citations",
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="citations",
    )
    snippet = models.TextField()
    page_number = models.PositiveIntegerField(null=True, blank=True)
    location_metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Citation for {self.answer_id}"
