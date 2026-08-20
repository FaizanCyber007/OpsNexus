from django.contrib import admin

from .models import Answer, AgentProfile, AgentRun, Citation, ToolCall


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "model_name", "temperature", "created_at")
    search_fields = ("name", "model_name")


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "agent_profile",
        "document",
        "status",
        "started_at",
        "finished_at",
    )
    list_filter = ("status", "agent_profile")


@admin.register(ToolCall)
class ToolCallAdmin(admin.ModelAdmin):
    list_display = ("tool_name", "agent_run", "created_at")
    list_filter = ("tool_name",)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "agent_run", "confidence_score", "is_verified", "created_at")
    list_filter = ("is_verified",)


@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = ("id", "answer", "document", "page_number")
