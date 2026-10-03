import logging
import re
import time
import uuid

from .logging import request_id_var

logger = logging.getLogger("nyayapath.request")
_SAFE_ID = re.compile(r"^[A-Za-z0-9\-_]{8,64}$")


class RequestContextMiddleware:
    """Attach a request id, and emit one structured log line per request (no query string/body)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.META.get("HTTP_X_REQUEST_ID", "")
        rid = incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex
        request.request_id = rid
        token = request_id_var.set(rid)
        start = time.monotonic()
        try:
            response = self.get_response(request)
        finally:
            duration = round((time.monotonic() - start) * 1000, 1)
            request_id_var.reset(token)
        response["X-Request-ID"] = rid
        user = getattr(request, "user", None)
        logger.info("request", extra={
            "endpoint": request.path, "method": request.method, "status_code": response.status_code,
            "duration_ms": duration, "service": "http",
            "user_id": str(user.pk) if user is not None and getattr(user, "is_authenticated", False) else None,
        })
        return response
