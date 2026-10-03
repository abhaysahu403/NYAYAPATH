import uuid

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
                             related_name="conversations")  # null = guest
    case = models.ForeignKey("cases.Case", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    title = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=5, default="en")
    context = models.JSONField(default=dict, blank=True)  # accumulated entities (state, district, topic, ...)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversations"
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["user", "-updated_at"])]


class MessageRole(models.TextChoices):
    USER = "USER", "User"
    ASSISTANT = "ASSISTANT", "Assistant"


class ConversationMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=MessageRole.choices)
    content = models.TextField()
    ai_response = models.ForeignKey("AIResponse", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "conversation_messages"
        ordering = ["created_at"]


class AIRequestType(models.TextChoices):
    CHAT = "CHAT", "Chat"
    INTAKE = "INTAKE", "Intake"
    DOCUMENT_ASK = "DOCUMENT_ASK", "Document question"
    DOCUMENT_ANALYZE = "DOCUMENT_ANALYZE", "Document analysis"
    JUDGMENT_EXPLAIN = "JUDGMENT_EXPLAIN", "Judgment explanation"
    ACTION_PLAN = "ACTION_PLAN", "Action plan"
    SIMILAR_CASES = "SIMILAR_CASES", "Similar cases"


class AIRequest(models.Model):
    """Metadata about an AI call. The raw prompt/question is NOT stored (privacy); only a hash + length."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="requests")
    request_type = models.CharField(max_length=20, choices=AIRequestType.choices)
    provider = models.CharField(max_length=30)
    model_name = models.CharField(max_length=80, blank=True)
    prompt_versions = models.JSONField(default=dict, blank=True)
    input_hash = models.CharField(max_length=64)
    input_chars = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, default="OK")  # OK | ERROR
    error_code = models.CharField(max_length=60, blank=True, null=True)
    latency_ms = models.PositiveIntegerField(default=0)
    llm_calls = models.PositiveIntegerField(default=0)
    cache_hits = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_requests"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"]), models.Index(fields=["request_type"])]


class AIResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.OneToOneField(AIRequest, on_delete=models.CASCADE, related_name="response")
    answer = models.TextField()
    language = models.CharField(max_length=5, default="en")
    verification_status = models.CharField(max_length=20, default="unverified")
    payload = models.JSONField(default=dict, blank=True)  # the full structured response object
    safety_flags = models.JSONField(default=list, blank=True)
    feedback_rating = models.SmallIntegerField(null=True, blank=True)  # -1 / 1
    feedback_comment = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_responses"


class CitationStatus(models.TextChoices):
    VERIFIED = "VERIFIED", "Matched a stored source"
    REJECTED = "REJECTED", "Could not be verified"


class Citation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.ForeignKey(AIResponse, on_delete=models.CASCADE, related_name="citations")
    source = models.ForeignKey("sources.Source", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    label = models.CharField(max_length=20)  # S1, S2 ...
    locator = models.CharField(max_length=200, blank=True, null=True)  # page / section
    status = models.CharField(max_length=10, choices=CitationStatus.choices)
    snapshot = models.JSONField(default=dict, blank=True)  # title/citation at answer time (survives deletion)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_citations"
