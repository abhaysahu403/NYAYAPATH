import uuid
from django.db import models


class CourtType(models.TextChoices):
    SUPREME_COURT = "SUPREME_COURT", "Supreme Court"
    HIGH_COURT = "HIGH_COURT", "High Court"
    DISTRICT_COURT = "DISTRICT_COURT", "District Court"
    SUBORDINATE_COURT = "SUBORDINATE_COURT", "Subordinate Court"
    TRIBUNAL = "TRIBUNAL", "Tribunal"
    OTHER = "OTHER", "Other"


class Court(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300)
    court_type = models.CharField(max_length=30, choices=CourtType.choices)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    official_identifier = models.CharField(max_length=100, blank=True, null=True, unique=True)
    website = models.URLField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courts"
        indexes = [
            models.Index(fields=["court_type"]),
            models.Index(fields=["state"]),
            models.Index(fields=["state", "district"]),
        ]
        ordering = ["court_type", "state", "name"]

    def __str__(self):
        return self.name
