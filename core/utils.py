import hashlib

from rest_framework.response import Response


def success_response(data=None, meta=None, status_code=200):
    payload = {"success": True, "data": data}
    if meta is not None:
        payload["meta"] = meta
    return Response(payload, status=status_code)


def get_client_ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    return fwd.split(",")[0].strip() if fwd else request.META.get("REMOTE_ADDR")


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
