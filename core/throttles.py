from rest_framework.throttling import SimpleRateThrottle


class _ScopedBase(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        ident = request.user.pk if request.user and request.user.is_authenticated else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class AuthThrottle(_ScopedBase):
    scope = "auth"


class AIChatThrottle(_ScopedBase):
    scope = "ai_chat"


class AIGuestThrottle(_ScopedBase):
    """Stricter limit that only applies to unauthenticated callers."""
    scope = "ai_guest"

    def allow_request(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        return super().allow_request(request, view)


class AIDocumentThrottle(_ScopedBase):
    scope = "ai_documents"


class JudgmentSearchThrottle(_ScopedBase):
    scope = "judgment_search"
AIHeavyThrottle = AIDocumentThrottle  # alias: expensive AI operations
