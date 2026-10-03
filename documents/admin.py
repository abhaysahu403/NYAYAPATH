from django.contrib import admin
from .models import Document, DocumentChunk, DocumentProcessingJob


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    fields = ["chunk_index", "page_number", "section_title"]
    readonly_fields = ["chunk_index", "page_number", "section_title"]
    can_delete = False
    max_num = 5


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["original_filename", "owner", "status", "mime_type", "file_size", "ocr_performed", "uploaded_at"]
    list_filter = ["status", "mime_type", "ocr_performed"]
    search_fields = ["original_filename", "owner__email"]
    raw_id_fields = ["owner", "case"]
    readonly_fields = ["checksum", "uploaded_at", "processed_at"]
    inlines = [DocumentChunkInline]


@admin.register(DocumentProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ["document", "status", "attempts", "error_code", "created_at", "finished_at"]
    list_filter = ["status"]
    readonly_fields = ["created_at", "started_at", "finished_at"]
