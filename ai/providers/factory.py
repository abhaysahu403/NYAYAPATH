from django.conf import settings

from core.exceptions import AINotConfiguredError


def get_ai_provider():
    """New instance per request so call statistics are per-request."""
    if settings.AI_PROVIDER == "mock":
        from ai.providers.mock import MockAIProvider
        return MockAIProvider()
    if settings.AI_PROVIDER == "gemini":
        from ai.providers.gemini import GeminiProvider
        return GeminiProvider()
    raise AINotConfiguredError(f"Unknown AI_PROVIDER '{settings.AI_PROVIDER}'.")


def get_embedding_provider():
    if settings.AI_PROVIDER == "mock":
        from ai.providers.mock import HashingEmbeddingProvider
        return HashingEmbeddingProvider()
    if settings.AI_PROVIDER == "gemini":
        from ai.providers.gemini import GeminiEmbeddingProvider
        return GeminiEmbeddingProvider()
    raise AINotConfiguredError(f"Unknown AI_PROVIDER '{settings.AI_PROVIDER}'.")
