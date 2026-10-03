"""Audit trail. Never stores document text, prompts or message bodies; auditing must never break a request."""
import logging
from typing import Optional

from audit.models import AuditEventType, AuditLog
from core.utils import get_client_ip

logger = logging.getLogger("nyayapath.audit")


def record(event_type: str, request=None, user=None, description: str = "", resource_type: Optional[str] = None,
           resource_id=None, metadata: Optional[dict] = None) -> Optional[AuditLog]:
    try:
        if user is None and request is not None and getattr(request, "user", None) is not None and request.user.is_authenticated:
            user = request.user
        if user is not None and not getattr(user, "is_authenticated", True):
            user = None
        ip = get_client_ip(request) if request is not None else None
        ua = request.META.get("HTTP_USER_AGENT", "")[:500] if request is not None else None
        return AuditLog.objects.create(
            user=user, event_type=event_type, description=(description or event_type)[:500], ip_address=ip or None,
            user_agent=ua or None, resource_type=resource_type, resource_id=str(resource_id) if resource_id else None,
            metadata=metadata or {})
    except Exception:  # noqa: BLE001
        logger.error("audit_write_failed", extra={"service": "audit", "event": str(event_type)})
        return None
