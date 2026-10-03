import uuid
from django.db import models
from django.conf import settings
from courts.models import Court
from sources.models import Source


class CaseStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    DISPOSED = "DISPOSED", "Disposed"
    DECIDED = "DECIDED", "Decided"
    TRANSFERRED = "TRANSFERRED", "Transferred"
    ABATED = "ABATED", "Abated"
    UNKNOWN = "UNKNOWN", "Unknown"


class CaseType(models.TextChoices):
    CIVIL = "CIVIL", "Civil"
    CRIMINAL = "CRIMINAL", "Criminal"
    WRIT = "WRIT", "Writ"
    APPEAL = "APPEAL", "Appeal"
    REVISION = "REVISION", "Revision"
    OTHER = "OTHER", "Other"


class CaseEventType(models.TextChoices):
    CASE_FILED = "CASE_FILED", "Case Filed"
    NOTICE_ISSUED = "NOTICE_ISSUED", "Notice Issued"
    HEARING = "HEARING", "Hearing"
    ORDER = "ORDER", "Order"
    JUDGMENT = "JUDGMENT", "Judgment"
    ADJOURNMENT = "ADJOURNMENT", "Adjournment"
    DOCUMENT_FILED = "DOCUMENT_FILED", "Document Filed"
    STATUS_CHANGE = "STATUS_CHANGE", "Status Change"
    OTHER = "OTHER", "Other"


class DataOrigin(models.TextChoices):
    """Who/what asserted this information (kept so facts are never confused with user claims)."""
    USER_PROVIDED = "USER_PROVIDED", "Provided by user"
    SOURCE_RECORD = "SOURCE_RECORD", "From an official/source record"
    DEMO = "DEMO", "Demo data"


class Case(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cases")
    cnr_number = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    case_number = models.CharField(max_length=100, blank=True, null=True)
    case_type = models.CharField(max_length=20, choices=CaseType.choices, default=CaseType.CIVIL)
    case_title = models.CharField(max_length=500, blank=True, null=True)
    court = models.ForeignKey(Court, on_delete=models.SET_NULL, null=True, blank=True, related_name="cases")
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    filing_year = models.PositiveIntegerField(blank=True, null=True)
    filing_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=CaseStatus.choices, default=CaseStatus.UNKNOWN)
    current_stage = models.CharField(max_length=255, blank=True, null=True)
    last_hearing_date = models.DateField(blank=True, null=True)
    next_hearing_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    data_origin = models.CharField(max_length=20, choices=DataOrigin.choices, default=DataOrigin.USER_PROVIDED)
    is_demo_data = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cases"
        indexes = [
            models.Index(fields=["cnr_number"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["state", "district"]),
        ]
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "cnr_number"], condition=models.Q(cnr_number__isnull=False),
                                    name="uniq_user_cnr"),
        ]

    def __str__(self):
        return f"{self.case_title or self.case_number or self.cnr_number or str(self.id)}"


class CaseParty(models.Model):
    PARTY_TYPES = [("PETITIONER", "Petitioner"), ("RESPONDENT", "Respondent"), ("INTERVENOR", "Intervenor"), ("OTHER", "Other")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="parties")
    party_type = models.CharField(max_length=20, choices=PARTY_TYPES)
    name = models.CharField(max_length=500)
    advocate = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "case_parties"

    def __str__(self):
        return f"{self.party_type}: {self.name}"


class CaseEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=20, choices=CaseEventType.choices)
    event_date = models.DateField()
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True)
    source_url = models.URLField(max_length=2000, blank=True, null=True)
    data_origin = models.CharField(max_length=20, choices=DataOrigin.choices, default=DataOrigin.USER_PROVIDED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "case_events"
        ordering = ["event_date"]
        indexes = [models.Index(fields=["case", "event_date"])]

    def __str__(self):
        return f"[{self.event_type}] {self.title} on {self.event_date}"


class Hearing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="hearings")
    hearing_date = models.DateField()
    purpose = models.CharField(max_length=300, blank=True, null=True)
    result = models.TextField(blank=True, null=True)
    next_date = models.DateField(blank=True, null=True)
    judge = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hearings"
        ordering = ["-hearing_date"]

    def __str__(self):
        return f"Hearing on {self.hearing_date} for {self.case}"
