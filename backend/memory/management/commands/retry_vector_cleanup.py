from django.core.management.base import BaseCommand

from memory.models import PendingVectorCleanup
from memory.vector_client import attempt_pending_cleanup


class Command(BaseCommand):
    help = "Retry ChromaDB vector deletions that failed on their first attempt."

    def handle(self, *args, **options):
        pending_records = list(PendingVectorCleanup.objects.all())
        succeeded = sum(
            1 for record in pending_records if attempt_pending_cleanup(record)
        )
        failed = len(pending_records) - succeeded
        self.stdout.write(
            self.style.SUCCESS(
                f"Retried {len(pending_records)} pending cleanup(s): "
                f"{succeeded} succeeded, {failed} still pending."
            )
        )
