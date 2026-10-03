import uuid
from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from pgvector.django import HnswIndex, VectorField


class DocumentStatus(models.TextChoices):
    UPLOADED = "UPLOADED", "Uploaded"
    PROCESSING = "PROCESSING", "Processing"
    TEXT_EXTRACTED = "TEXT_EXTRACTED", "Text Extracted"
    OCR_REQUIRED = "OCR_REQUIRED", "OCR Required"
    INDEXED = "INDEXED", "Indexed"
    FAILED = "FAILED", "Failed"
    ANALYZED = "ANALYZED", "Analyzed"


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    original_filename = models.CharField(max_length=500)
    stored_filename = models.CharField(max_length=500)
    file_path = models.CharField(max_length=1000)
    mime_type = models.CharField(max_length=100)
    file_size = models.PositiveBigIntegerField()
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.UPLOADED)
    extracted_text = models.TextField(blank=True, null=True)
    ocr_performed = models.BooleanField(default=False)
    page_count = models.PositiveIntegerField(blank=True, null=True)
    checksum = models.CharField(max_length=64, blank=True, null=True)
    case = models.ForeignKey("cases.Case", on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    source = models.ForeignKey("sources.Source", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    analysis_result = models.JSONField(default=dict, blank=True)
    processing_error = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "documents"
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["uploaded_at"]),
        ]
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"


class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    page_number = models.PositiveIntegerField(blank=True, null=True)
    section_title = models.CharField(max_length=500, blank=True, null=True)
    char_start = models.PositiveIntegerField(blank=True, null=True)
    char_end = models.PositiveIntegerField(blank=True, null=True)
    chunk_metadata = models.JSONField(default=dict, blank=True)
    embedding = VectorField(dimensions=settings.EMBEDDING_DIM, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "document_chunks"
        ordering = ["document", "chunk_index"]
        unique_together = [("document", "chunk_index")]
        indexes = [
            GinIndex(SearchVector("text", config="simple"), name="dc_text_fts_idx"),
            HnswIndex(name="dc_embedding_hnsw_idx", fields=["embedding"], m=16, ef_construction=64,
                      opclasses=["vector_cosine_ops"]),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.original_filename}"


class ProcessingJobStatus(models.TextChoices):
    QUEUED = "QUEUED", "Queued"
    RUNNING = "RUNNING", "Running"
    SUCCEEDED = "SUCCEEDED", "Succeeded"
    FAILED = "FAILED", "Failed"


class DocumentProcessingJob(models.Model):
    """One processing attempt. A task queue (Celery) can later pick these up instead of sync execution."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="jobs")
    status = models.CharField(max_length=12, choices=ProcessingJobStatus.choices, default=ProcessingJobStatus.QUEUED)
    attempts = models.PositiveIntegerField(default=0)
    error_code = models.CharField(max_length=60, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "document_processing_jobs"
        ordering = ["-created_at"]
