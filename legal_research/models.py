import uuid

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.db import models
from pgvector.django import HnswIndex, VectorField


class KnowledgeChunk(models.Model):
    """Searchable passage of a Source (judgment text, statute overview, official guide...).

    Hybrid search runs over this table: pgvector similarity + Postgres full-text + metadata filters.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey("sources.Source", on_delete=models.CASCADE, related_name="chunks")
    judgment = models.ForeignKey("judgments.Judgment", on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    section_title = models.CharField(max_length=500, blank=True, null=True)
    page_number = models.PositiveIntegerField(blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    topics = models.JSONField(default=list, blank=True)
    language = models.CharField(max_length=5, default="en")
    content_hash = models.CharField(max_length=64, blank=True, null=True)
    embedding = VectorField(dimensions=settings.EMBEDDING_DIM, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_chunks"
        unique_together = [("source", "chunk_index")]
        indexes = [
            models.Index(fields=["state"]),
            GinIndex(SearchVector("text", config="simple"), name="kc_text_fts_idx"),
            HnswIndex(name="kc_embedding_hnsw_idx", fields=["embedding"], m=16, ef_construction=64,
                      opclasses=["vector_cosine_ops"]),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.source_id}"


class SearchKind(models.TextChoices):
    JUDGMENT = "JUDGMENT", "Judgment search"
    SIMILAR_CASE = "SIMILAR_CASE", "Similar case search"
    RESEARCH = "RESEARCH", "Legal research"


class SearchQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
                             related_name="search_queries")
    kind = models.CharField(max_length=20, choices=SearchKind.choices, default=SearchKind.JUDGMENT)
    query_text = models.TextField()
    rewritten_queries = models.JSONField(default=list, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    language = models.CharField(max_length=10, blank=True, null=True)
    result_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "search_queries"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]


class ResearchResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    search_query = models.ForeignKey(SearchQuery, on_delete=models.CASCADE, related_name="results")
    source = models.ForeignKey("sources.Source", on_delete=models.CASCADE, related_name="+")
    judgment = models.ForeignKey("judgments.Judgment", on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="+")
    rank = models.PositiveIntegerField()
    relevance_score = models.FloatField()  # relative within one result set; NOT legal certainty
    relevance_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "research_results"
        ordering = ["search_query", "rank"]
