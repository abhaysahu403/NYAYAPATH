"""Google Gemini provider (google-genai SDK). Not exercised by the automated tests (they use the mock)."""
import logging
import math
from typing import List

from django.conf import settings

from ai.providers.base import EmbeddingProvider, LLMProvider
from core.exceptions import AINotConfiguredError, AIServiceError

logger = logging.getLogger("nyayapath.ai")


def _client():
    if not settings.GEMINI_API_KEY:
        raise AINotConfiguredError("GEMINI_API_KEY is not set.")
    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover
        raise AINotConfiguredError("google-genai is not installed.") from exc
    return genai


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self):
        super().__init__()
        self.model = settings.GEMINI_MODEL
        self._genai = _client()
        self._client = self._genai.Client(api_key=settings.GEMINI_API_KEY)

    def _complete(self, prompt: str, max_tokens: int) -> str:
        from google.genai import types
        try:
            resp = self._client.models.generate_content(
                model=self.model, contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1, max_output_tokens=max_tokens, response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_budget=0)),
            )
            return resp.text or ""
        except Exception as exc:  # noqa: BLE001
            logger.error("gemini_call_failed", extra={"error_type": type(exc).__name__, "service": "gemini"})
            raise AIServiceError() from exc


class GeminiEmbeddingProvider(EmbeddingProvider):
    name = "gemini"

    def __init__(self):
        self._genai = _client()
        self._client = self._genai.Client(api_key=settings.GEMINI_API_KEY)

    def embed_texts(self, texts: List[str], *, query: bool = False) -> List[List[float]]:
        from google.genai import types
        out: List[List[float]] = []
        try:
            for i in range(0, len(texts), 50):
                resp = self._client.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL, contents=texts[i:i + 50],
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_QUERY" if query else "RETRIEVAL_DOCUMENT",
                        output_dimensionality=self.dimensions))
                for e in resp.embeddings:
                    v = list(e.values)
                    n = math.sqrt(sum(x * x for x in v)) or 1.0
                    out.append([x / n for x in v])
        except Exception as exc:  # noqa: BLE001
            logger.error("gemini_embed_failed", extra={"error_type": type(exc).__name__, "service": "gemini"})
            raise AIServiceError("Embedding generation failed.") from exc
        return out
