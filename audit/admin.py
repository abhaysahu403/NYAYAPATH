from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["event_type", "user", "resource_type", "resource_id", "ip_address", "created_at"]
    list_filter = ["event_type", "resource_type"]
    search_fields = ["user__email", "resource_id", "description"]
    readonly_fields = list(map(str, ["event_type","user","description","ip_address","user_agent",
                                      "resource_type","resource_id","metadata","created_at"]))
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
