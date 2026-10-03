from django.core.management.base import BaseCommand

from documents.models import Document, DocumentChunk
from documents.processing import embed_document_chunks
from legal_research.models import KnowledgeChunk
from legal_research.services.indexing import embed_pending


class Command(BaseCommand):
    help = "Generate missing embeddings (knowledge + document chunks). --rebuild clears all vectors first (use after changing provider)."

    def add_arguments(self, p):
        p.add_argument("--rebuild", action="store_true")

    def handle(self, *a, **o):
        if o["rebuild"]:
            KnowledgeChunk.objects.update(embedding=None); DocumentChunk.objects.update(embedding=None)
        n = embed_pending()
        for d in Document.objects.filter(chunks__embedding__isnull=True).distinct():
            n += embed_document_chunks(d)
        self.stdout.write(self.style.SUCCESS(f"Embedded {n} chunks"))
