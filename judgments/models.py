import uuid
from django.db import models
from courts.models import Court
from sources.models import Source


class LegalTopic(models.TextChoices):
    LAND_DISPUTE = "LAND_DISPUTE", "Land Dispute"
    PROPERTY_DISPUTE = "PROPERTY_DISPUTE", "Property Dispute"
    CIVIL_DISPUTE = "CIVIL_DISPUTE", "Civil Dispute"
    CASE_PENDENCY = "CASE_PENDENCY", "Case Pendency"
    COURT_PROCEDURE = "COURT_PROCEDURE", "Court Procedure"
    RTI = "RTI", "Right to Information"
    CRIMINAL_CASE = "CRIMINAL_CASE", "Criminal Case"
    BAIL = "BAIL", "Bail"
    FAMILY_DISPUTE = "FAMILY_DISPUTE", "Family Dispute"
    CONSUMER_DISPUTE = "CONSUMER_DISPUTE", "Consumer Dispute"
    LABOUR_DISPUTE = "LABOUR_DISPUTE", "Labour Dispute"
    GOVERNMENT_SERVICE = "GOVERNMENT_SERVICE", "Government Service"
    MOTOR_ACCIDENT = "MOTOR_ACCIDENT", "Motor Accident"
    CONSTITUTIONAL = "CONSTITUTIONAL", "Constitutional Matter"
    OTHER = "OTHER", "Other"


class EmbeddingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    INDEXED = "INDEXED", "Indexed"
    FAILED = "FAILED", "Failed"
    NOT_REQUIRED = "NOT_REQUIRED", "Not Required"


class VerificationStatus(models.TextChoices):
    UNVERIFIED = "UNVERIFIED", "Unverified"
    VERIFIED = "VERIFIED", "Verified"
    DEMO = "DEMO", "Demo Data"


class Judgment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    court = models.ForeignKey(Court, on_delete=models.SET_NULL, null=True, blank=True, related_name="judgments")
    citation = models.CharField(max_length=300, blank=True, null=True, db_index=True)
    case_number = models.CharField(max_length=200, blank=True, null=True)
    judgment_date = models.DateField(blank=True, null=True)
    bench = models.TextField(blank=True, null=True)
    petitioner = models.CharField(max_length=500, blank=True, null=True)
    respondent = models.CharField(max_length=500, blank=True, null=True)
    legal_topics = models.JSONField(default=list)
    summary = models.TextField(blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)
    source_url = models.URLField(max_length=2000, blank=True, null=True)
    document_url = models.URLField(max_length=2000, blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    language = models.CharField(max_length=5, default="en")
    keywords = models.JSONField(default=list, blank=True)
    embedding_status = models.CharField(max_length=20, choices=EmbeddingStatus.choices, default=EmbeddingStatus.PENDING)
    verification_status = models.CharField(max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.UNVERIFIED)
    is_demo_data = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "judgments"
        indexes = [
            models.Index(fields=["citation"]),
            models.Index(fields=["judgment_date"]),
            models.Index(fields=["state"]),
            models.Index(fields=["verification_status"]),
        ]
        ordering = ["-judgment_date"]

    def __str__(self):
        return f"{self.title} ({self.citation or 'No citation'})"
