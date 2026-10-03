from django.core.management.base import BaseCommand

from documents.models import Document, DocumentStatus
from documents.processing import process_document


class Command(BaseCommand):
    help = "(Re)process uploaded documents that are not indexed (UPLOADED / FAILED / OCR_REQUIRED). Worker-style entry point."

    def add_arguments(self, p):
        p.add_argument("--all", action="store_true")

    def handle(self, *a, **o):
        qs = Document.objects.all() if o["all"] else Document.objects.filter(
            status__in=[DocumentStatus.UPLOADED, DocumentStatus.FAILED, DocumentStatus.OCR_REQUIRED])
        ok = sum(1 for d in qs if process_document(str(d.id)))
        self.stdout.write(self.style.SUCCESS(f"Processed {ok}/{qs.count()} documents"))
