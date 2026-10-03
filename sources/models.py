import uuid
from django.db import models


class SourceType(models.TextChoices):
    OFFICIAL_COURT = "OFFICIAL_COURT", "Official Court Record"
    GOVERNMENT = "GOVERNMENT", "Government Source"
    JUDGMENT = "JUDGMENT", "Judgment"
    CASE_RECORD = "CASE_RECORD", "Case Record"
    USER_DOCUMENT = "USER_DOCUMENT", "User Uploaded Document"
    LEGAL_INFORMATION = "LEGAL_INFORMATION", "Legal Information"
    OTHER = "OTHER", "Other"


class VerificationStatus(models.TextChoices):
    UNVERIFIED = "UNVERIFIED", "Unverified"
    VERIFIED = "VERIFIED", "Verified"
    FAILED = "FAILED", "Verification Failed"
    PENDING = "PENDING", "Pending Verification"


class Source(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=2000, blank=True, null=True)
    court = models.CharField(max_length=300, blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    retrieved_at = models.DateTimeField(auto_now_add=True)
    source_updated_at = models.DateTimeField(blank=True, null=True)
    identifier = models.CharField(max_length=300, blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.UNVERIFIED)
    content_hash = models.CharField(max_length=64, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_demo_data = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    verification_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sources"
        indexes = [
            models.Index(fields=["source_type"]),
            models.Index(fields=["verification_status"]),
            models.Index(fields=["identifier"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["source_type", "identifier"], condition=models.Q(identifier__isnull=False),
                                    name="uniq_source_type_identifier"),
        ]

    def __str__(self):
        return f"[{self.source_type}] {self.title}"
