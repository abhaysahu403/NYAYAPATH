"""Index judgment / source text into KnowledgeChunk rows (chunk -> embed). Idempotent via content hash."""
import logging
from typing import Optional

from ai.embedding import EmbeddingService
from core.text import chunk_pages
from core.utils import sha256_text
from judgments.models import EmbeddingStatus, Judgment
from legal_research.models import KnowledgeChunk
from sources.models import Source

logger = logging.getLogger("nyayapath.indexing")


def index_text(source: Source, text: str, judgment: Optional[Judgment] = None, state=None, topics=None,
               language="en", force=False) -> int:
    digest = sha256_text(text)
    existing = KnowledgeChunk.objects.filter(source=source)
    if not force and existing.exists() and source.content_hash == digest and not existing.filter(embedding__isnull=True).exists():
        return 0
    existing.delete()
    chunks = chunk_pages([(None, text)], max_chars=1000, min_chars=80)
    rows = [KnowledgeChunk(source=source, judgment=judgment, chunk_index=i, text=c.text, section_title=c.section_title,
                           page_number=c.page_number, state=state, topics=topics or [], language=language,
                           content_hash=sha256_text(c.text)) for i, c in enumerate(chunks)]
    KnowledgeChunk.objects.bulk_create(rows)
    source.content_hash = digest
    source.save(update_fields=["content_hash"])
    embed_pending(source=source)
    return len(rows)


def embed_pending(source: Optional[Source] = None, batch: int = 50) -> int:
    qs = KnowledgeChunk.objects.filter(embedding__isnull=True)
    if source:
        qs = qs.filter(source=source)
    chunks = list(qs.order_by("source_id", "chunk_index"))
    svc, n = EmbeddingService(), 0
    for i in range(0, len(chunks), batch):
        part = chunks[i:i + batch]
        try:
            vecs = svc.embed_documents([c.text for c in part])
        except Exception as exc:  # noqa: BLE001
            logger.error("embed_batch_failed", extra={"service": "indexing", "error_type": type(exc).__name__})
            continue
        for c, v in zip(part, vecs):
            c.embedding = v
        KnowledgeChunk.objects.bulk_update(part, ["embedding"])
        n += len(part)
    return n


def index_judgment(j: Judgment, force=False) -> int:
    text = j.full_text or j.summary
    if not text or not j.source:
        j.embedding_status = EmbeddingStatus.NOT_REQUIRED
        j.save(update_fields=["embedding_status"])
        return 0
    n = index_text(j.source, text, judgment=j, state=j.state, topics=j.legal_topics, language=j.language, force=force)
    j.embedding_status = EmbeddingStatus.INDEXED
    j.save(update_fields=["embedding_status"])
    return n
