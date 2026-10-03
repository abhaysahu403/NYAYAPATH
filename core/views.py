import logging

from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from core.utils import success_response
from judgments.models import LegalTopic

logger = logging.getLogger("nyayapath.health")


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request):
        db, vector = "connected", "available"
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
                cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                if cur.fetchone() is None:
                    vector = "missing"
        except Exception:  # noqa: BLE001 - report state, never details
            logger.error("health_db_failure")
            db, vector = "unavailable", "unknown"
        healthy = db == "connected"
        return success_response({"status": "healthy" if healthy else "degraded", "database": db, "pgvector": vector,
                                 "version": "1.0.0"}, status_code=200 if healthy else 503)


class LegalTopicListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return success_response([{"code": c, "label": l} for c, l in LegalTopic.choices])
