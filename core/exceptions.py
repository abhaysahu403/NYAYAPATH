"""Consistent error format: {"success": false, "error": {"code", "message", "details?"}}."""
import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions as drf_exc, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("nyayapath.errors")


class NyayaError(Exception):
    """Domain error with a stable machine-readable code."""
    status_code = status.HTTP_400_BAD_REQUEST
    code = "BAD_REQUEST"
    message = "The request could not be processed."

    def __init__(self, message=None, code=None, status_code=None, details=None):
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.details = details
        super().__init__(self.message)


class NotFoundError(NyayaError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"
    message = "The requested resource could not be found."


class AINotConfiguredError(NyayaError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "AI_NOT_CONFIGURED"
    message = "The AI provider is not configured."


class AIServiceError(NyayaError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "AI_UNAVAILABLE"
    message = "The AI service could not complete the request. Please try again."


_CODE_MAP = {
    drf_exc.ValidationError: "VALIDATION_ERROR",
    drf_exc.NotAuthenticated: "NOT_AUTHENTICATED",
    drf_exc.AuthenticationFailed: "AUTHENTICATION_FAILED",
    drf_exc.PermissionDenied: "PERMISSION_DENIED",
    drf_exc.NotFound: "NOT_FOUND",
    drf_exc.MethodNotAllowed: "METHOD_NOT_ALLOWED",
    drf_exc.Throttled: "RATE_LIMITED",
    drf_exc.ParseError: "INVALID_REQUEST_BODY",
    drf_exc.UnsupportedMediaType: "UNSUPPORTED_MEDIA_TYPE",
}


def _flatten(detail):
    """Return (message, details) from DRF error detail."""
    if isinstance(detail, dict):
        details = {k: [str(i) for i in (v if isinstance(v, list) else [v])] for k, v in detail.items()}
        key = next(iter(details))
        return f"{key}: {details[key][0]}" if key != "non_field_errors" else details[key][0], details
    if isinstance(detail, list):
        return (str(detail[0]) if detail else "Invalid input."), None
    return str(detail), None


def _body(code, message, details=None):
    err = {"code": code, "message": message}
    if details:
        err["details"] = details
    return {"success": False, "error": err}


def api_exception_handler(exc, context):
    if isinstance(exc, NyayaError):
        return Response(_body(exc.code, exc.message, exc.details), status=exc.status_code)
    if isinstance(exc, Http404):
        exc = drf_exc.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = drf_exc.PermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        exc = drf_exc.ValidationError(exc.messages)

    response = exception_handler(exc, context)
    if response is not None:
        code = next((c for k, c in _CODE_MAP.items() if isinstance(exc, k)), "ERROR")
        message, details = _flatten(getattr(exc, "detail", str(exc)))
        if isinstance(exc, drf_exc.Throttled):
            message = "Too many requests. Please slow down and try again later."
            if exc.wait:
                response["Retry-After"] = str(int(exc.wait))
                details = {"retry_after_seconds": int(exc.wait)}
        response.data = _body(code, message, details)
        return response

    # Unhandled: never leak internals.
    view = context.get("view")
    logger.error("unhandled_exception", exc_info=exc,
                 extra={"service": view.__class__.__name__ if view else None, "error_type": type(exc).__name__})
    return Response(_body("INTERNAL_ERROR", "An unexpected error occurred."), status=500)


class ValidationError(NyayaError):
    """Input validation failure. `detail` may be a serializer.errors dict."""
    status_code = status.HTTP_400_BAD_REQUEST
    code = "VALIDATION_ERROR"
    message = "The submitted data is invalid."

    def __init__(self, message=None, detail=None, code=None):
        details = None
        if detail:
            details = {k: ([str(i) for i in v] if isinstance(v, (list, tuple)) else [str(v)]) for k, v in dict(detail).items()} \
                if isinstance(detail, dict) else {"error": [str(detail)]}
            if message is None:
                key = next(iter(details))
                message = f"{key}: {details[key][0]}"
        super().__init__(message=message, code=code, details=details)


class AuthenticationError(NyayaError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "AUTHENTICATION_FAILED"
    message = "Authentication failed."


class PermissionDeniedError(NyayaError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "PERMISSION_DENIED"
    message = "You do not have access to this resource."
