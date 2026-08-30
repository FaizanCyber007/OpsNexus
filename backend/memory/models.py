from django.db import models

from core.models import BaseModel


class PendingVectorCleanup(BaseModel):
    """Durable record of a ChromaDB vector deletion that still needs to happen.

    Written synchronously (same transaction as the Document change that
    triggered it -- see documents/signals.py) so a rollback removes the
    pending record too. A best-effort delete is attempted immediately after
    commit; if it fails, this row survives so `retry_vector_cleanup` can try
    again later instead of the failure being silently logged and discarded.
    """

    document_id = models.UUIDField(db_index=True)
    organization_id = models.UUIDField(db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Pending cleanup for document {self.document_id}"
