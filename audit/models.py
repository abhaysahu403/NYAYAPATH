import uuid
from django.db import models
from django.conf import settings


class AuditEventType(models.TextChoices):
    USER_REGISTERED = "USER_REGISTERED", "User Registered"
    USER_LOGIN = "USER_LOGIN", "User Login"
    USER_LOGOUT = "USER_LOGOUT", "User Logout"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED", "Document Uploaded"
    DOCUMENT_ACCESSED = "DOCUMENT_ACCESSED", "Document Accessed"
    DOCUMENT_DELETED = "DOCUMENT_DELETED", "Document Deleted"
    AI_REQUEST = "AI_REQUEST", "AI Request"
    ACTION_PLAN_CREATED = "ACTION_PLAN_CREATED", "Action Plan Created"
    DRAFT_CREATED = "DRAFT_CREATED", "Draft Created"
    CASE_CREATED = "CASE_CREATED", "Case Created"
    ADMIN_ACTION = "ADMIN_ACTION", "Admin Action"
    SOURCE_INGESTED = "SOURCE_INGESTED", "Source Ingested"
    LOGIN_FAILED = "LOGIN_FAILED", "Login Failed"
    PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"
    CASE_UPDATED = "CASE_UPDATED", "Case Updated"
    CASE_DELETED = "CASE_DELETED", "Case Deleted"
    DOCUMENT_ANALYZED = "DOCUMENT_ANALYZED", "Document Analyzed"
    DOCUMENT_LINK_ISSUED = "DOCUMENT_LINK_ISSUED", "Document Download Link Issued"
    SEARCH = "SEARCH", "Research Search"
    ACTION_STEP_UPDATED = "ACTION_STEP_UPDATED", "Action Step Updated"
    CONVERSATION_DELETED = "CONVERSATION_DELETED", "Conversation Deleted"
    SOURCE_VERIFIED = "SOURCE_VERIFIED", "Source Verified"
    SOURCE_MODIFIED = "SOURCE_MODIFIED", "Source Modified"
    AI_CHAT = "AI_CHAT", "AI Chat"
    USER_PASSWORD_CHANGE = "USER_PASSWORD_CHANGE", "Password Changed"
    ACTION_PLAN_GENERATED = "ACTION_PLAN_GENERATED", "Action Plan Generated"
    DRAFT_GENERATED = "DRAFT_GENERATED", "Draft Generated"
    JUDGMENT_EXPLAINED = "JUDGMENT_EXPLAINED", "Judgment Explained"
    OTHER = "OTHER", "Other"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=40, choices=AuditEventType.choices)
    description = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    resource_type = models.CharField(max_length=100, blank=True, null=True)
    resource_id = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.event_type}] {self.description}"
