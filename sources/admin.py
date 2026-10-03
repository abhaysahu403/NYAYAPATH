from django.contrib import admin
from .models import Source

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ["title", "source_type", "court", "verification_status", "is_demo_data", "retrieved_at"]
    list_filter = ["source_type", "verification_status", "is_demo_data"]
    search_fields = ["title", "url", "identifier"]
    readonly_fields = ["content_hash", "retrieved_at"]
