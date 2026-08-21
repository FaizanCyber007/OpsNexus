from django.core.management.base import BaseCommand

from memory.models import PendingVectorCleanup
from memory.vector_client import attempt_pending_cleanup


class Command(BaseCommand):
    help = "Retry ChromaDB vector deletions that failed on their first attempt."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of pending records to process in this invocation.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of records to fetch per database batch (default 100).",
        )

    def handle(self, *args, **options):
        limit = options.get("limit")
        batch_size = options.get("batch_size") or 100

        queryset = PendingVectorCleanup.objects.all().order_by("created_at")
        if limit is not None and limit > 0:
            # Materialize IDs for the sliced subset so iterator can be used safely
            target_ids = list(queryset.values_list("id", flat=True)[:limit])
            queryset = PendingVectorCleanup.objects.filter(id__in=target_ids).order_by(
                "created_at"
            )

        total = 0
        succeeded = 0
        for record in queryset.iterator(chunk_size=batch_size):
            total += 1
            if attempt_pending_cleanup(record):
                succeeded += 1

        failed = total - succeeded
        self.stdout.write(
            self.style.SUCCESS(
                f"Retried {total} pending cleanup(s): "
                f"{succeeded} succeeded, {failed} still pending."
            )
        )
