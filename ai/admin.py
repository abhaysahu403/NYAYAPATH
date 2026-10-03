from django.contrib import admin
from .models import Conversation, ConversationMessage, AIRequest, AIResponse, Citation

class MessageInline(admin.TabularInline):
    model = ConversationMessage
    extra = 0
    fields = ["role", "content", "created_at"]
    readonly_fields = ["created_at"]
    can_delete = False
    max_num = 10

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "language", "created_at", "updated_at"]
    list_filter = ["language"]
    raw_id_fields = ["user", "case"]
    inlines = [MessageInline]

@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "request_type", "provider", "status", "llm_calls", "latency_ms", "created_at"]
    list_filter = ["request_type", "status", "provider"]
    readonly_fields = ["created_at"]

@admin.register(AIResponse)
class AIResponseAdmin(admin.ModelAdmin):
    list_display = ["id", "request", "language", "verification_status", "created_at"]
    list_filter = ["verification_status", "language"]
    readonly_fields = ["created_at"]
