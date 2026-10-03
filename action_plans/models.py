import uuid
from django.db import models
from django.conf import settings
from cases.models import Case


class ActionPlanStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"
    ARCHIVED = "ARCHIVED", "Archived"


class ActionStepStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    SKIPPED = "SKIPPED", "Skipped"


class ActionPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="action_plans")
    case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True, related_name="action_plans")
    title = models.CharField(max_length=500)
    situation_assessment = models.TextField()
    delay_cause_analysis = models.TextField(blank=True, null=True)
    immediate_priority = models.TextField(blank=True, null=True)
    warnings = models.JSONField(default=list)
    supporting_sources = models.JSONField(default=list)
    original_query = models.TextField()
    intake_analysis = models.JSONField(default=dict)
    evidence = models.JSONField(default=dict, blank=True)
    language = models.CharField(max_length=5, default="en")
    status = models.CharField(max_length=20, choices=ActionPlanStatus.choices, default=ActionPlanStatus.ACTIVE)
    disclaimer = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "action_plans"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ActionStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_plan = models.ForeignKey(ActionPlan, on_delete=models.CASCADE, related_name="steps")
    step_number = models.PositiveIntegerField()
    title = models.CharField(max_length=300)
    description = models.TextField()
    why_relevant = models.TextField(blank=True, null=True)
    documents_needed = models.JSONField(default=list)
    legal_basis = models.CharField(max_length=500, blank=True, null=True)
    estimated_timeline = models.CharField(max_length=200, blank=True, null=True)
    difficulty = models.CharField(max_length=20, default="MEDIUM")
    source_references = models.JSONField(default=list)
    kind = models.CharField(max_length=30, default="POSSIBLE_OPTION")  # POSSIBLE_OPTION | INFORMATION_GATHERING
    source_backed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=ActionStepStatus.choices, default=ActionStepStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "action_steps"
        ordering = ["action_plan", "step_number"]
        unique_together = [("action_plan", "step_number")]

    def __str__(self):
        return f"Step {self.step_number}: {self.title}"
