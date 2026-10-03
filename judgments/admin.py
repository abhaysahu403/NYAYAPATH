from django.contrib import admin
from .models import Judgment

@admin.register(Judgment)
class JudgmentAdmin(admin.ModelAdmin):
    list_display = ["title", "citation", "court", "judgment_date", "verification_status", "is_demo_data", "embedding_status"]
    list_filter = ["verification_status", "is_demo_data", "embedding_status", "state"]
    search_fields = ["title", "citation", "petitioner", "respondent"]
    raw_id_fields = ["court", "source"]
    readonly_fields = ["created_at", "updated_at"]
