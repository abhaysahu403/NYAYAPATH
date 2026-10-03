from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    """Wrap every successful response as {"success": true, "data": ..., "meta": ...}."""
    charset = "utf-8"
    ensure_ascii = False  # keep Devanagari readable

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        if response is not None and response.status_code < 400 and response.status_code != 204:
            already = isinstance(data, dict) and "success" in data
            if not already:
                data = {"success": True, "data": data}
        elif response is not None and response.status_code >= 400:
            if not (isinstance(data, dict) and data.get("success") is False):
                detail = data.get("detail") if isinstance(data, dict) else None
                data = {"success": False, "error": {"code": "ERROR", "message": str(detail or "Request failed.")}}
        return super().render(data, accepted_media_type, renderer_context)
NyayaRenderer = EnvelopeJSONRenderer  # backwards-compatible alias used by views
