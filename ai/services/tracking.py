"""AIRequest / AIResponse bookkeeping. Stores a hash + length of the input, never the raw prompt (privacy)."""
import logging
import time
from typing import Optional

from core.text import clean_text  # noqa: F401  (kept for callers that normalise before hashing)
from core.utils import sha256_text
from ai.models import AIRequest, AIResponse

logger = logging.getLogger("nyayapath.ai.tracking")


class AICall:
    def __init__(self, user, request_type: str, provider, input_text: str, conversation=None):
        self.user = user if (user is not None and getattr(user, "is_authenticated", False)) else None
        self.request_type = request_type
        self.provider = provider
        self.conversation = conversation
        self.input_hash = sha256_text(input_text or "")
        self.input_chars = len(input_text or "")
        self.started = time.monotonic()
        self.request: Optional[AIRequest] = None

    def _base(self, status: str, error_code: Optional[str] = None) -> Optional[AIRequest]:
        try:
            st = getattr(self.provider, "stats", None)
            self.request = AIRequest.objects.create(
                user=self.user, conversation=self.conversation, request_type=self.request_type,
                provider=getattr(self.provider, "name", "unknown"), model_name=getattr(self.provider, "model", "") or "",
                prompt_versions=dict(st.prompt_versions) if st else {}, input_hash=self.input_hash,
                input_chars=self.input_chars, status=status, error_code=error_code,
                latency_ms=int((time.monotonic() - self.started) * 1000),
                llm_calls=st.llm_calls if st else 0, cache_hits=st.cache_hits if st else 0)
        except Exception:  # noqa: BLE001 - tracking must never break a request
            logger.error("ai_track_failed", extra={"service": "ai_tracking"})
        return self.request

    def success(self, answer: str, language: str, verification_status: str, payload: dict, safety_flags=None):
        req = self._base("OK")
        if req is None:
            return None
        try:
            return AIResponse.objects.create(request=req, answer=answer, language=language[:5],
                                             verification_status=verification_status[:20], payload=payload,
                                             safety_flags=safety_flags or [])
        except Exception:  # noqa: BLE001
            logger.error("ai_track_response_failed", extra={"service": "ai_tracking"})
            return None

    def failure(self, error_code: str):
        self._base("ERROR", error_code[:60])
