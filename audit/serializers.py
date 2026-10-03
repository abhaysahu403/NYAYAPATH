from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = ["id", "user", "user_email", "event_type", "description", "ip_address", "resource_type",
                  "resource_id", "metadata", "created_at"]
