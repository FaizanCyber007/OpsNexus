from django.db import models

from core.models import BaseModel, Organization


class Document(BaseModel):
    class DocType(models.TextChoices):
        SECURITY_QUESTIONNAIRE = "security_questionnaire", "Security Questionnaire"
        INVOICE = "invoice", "Invoice"
        COMPLIANCE_LOG = "compliance_log", "Compliance Log"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    file_path = models.CharField(max_length=1024)

    def __str__(self):
        return f"{self.get_doc_type_display()} ({self.status})"
