from django.contrib import admin
from .models import GeneratedDraft

@admin.register(GeneratedDraft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ["title", "draft_type", "user", "language", "created_at"]
    list_filter = ["draft_type", "language"]
    search_fields = ["title", "user__email"]
    raw_id_fields = ["user", "case"]
    readonly_fields = ["created_at", "updated_at", "placeholders_used", "field_provenance", "source_references"]
