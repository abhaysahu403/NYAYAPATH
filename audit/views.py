from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from core.pagination import StandardPagination
from core.permissions import IsAdminUser
from core.renderers import NyayaRenderer
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogView(APIView):
    """Admin-only audit log listing."""
    permission_classes = [IsAuthenticated, IsAdminUser]
    renderer_classes = [NyayaRenderer]

    def get(self, request):
        qs = AuditLog.objects.select_related("user").order_by("-created_at")
        event_type = request.query_params.get("event_type")
        user_id = request.query_params.get("user_id")
        resource_type = request.query_params.get("resource_type")
        if event_type:
            qs = qs.filter(event_type=event_type)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AuditLogSerializer(page, many=True).data)
