import uuid
from django.db import models
from django.conf import settings
from cases.models import Case


class DraftType(models.TextChoices):
    CASE_SUMMARY = "CASE_SUMMARY", "Case Summary"
    LAWYER_BRIEF = "LAWYER_BRIEF", "Lawyer Brief"
    RTI_APPLICATION = "RTI_APPLICATION", "RTI Application"
    GENERAL_APPLICATION = "GENERAL_APPLICATION", "General Application"


class GeneratedDraft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="drafts")
    case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name="drafts")
    draft_type = models.CharField(max_length=30, choices=DraftType.choices)
    title = models.CharField(max_length=500)
    content_english = models.TextField()
    content_hindi = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=5, default="en")
    placeholders_used = models.JSONField(default=list)
    field_provenance = models.JSONField(default=dict)  # field -> USER_PROVIDED | CASE_RECORD | UNKNOWN
    source_references = models.JSONField(default=list)
    filing_instructions = models.TextField(blank=True, null=True)
    important_notes = models.JSONField(default=list)
    source_intake = models.JSONField(default=dict)
    disclaimer = models.TextField(default=(
        "This draft is generated for informational purposes only. "
        "It is NOT a legally valid filing. Verify all details with a "
        "qualified legal professional before use."
    ))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "generated_drafts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.draft_type}] {self.title}"
