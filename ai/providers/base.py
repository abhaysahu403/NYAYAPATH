"""Provider abstraction. Services depend on AIProviderInterface / EmbeddingProvider, never on a vendor SDK."""
import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from django.conf import settings
from django.core.cache import cache

from ai.prompts.registry import render
from core.exceptions import AIServiceError, NyayaError

logger = logging.getLogger("nyayapath.ai")


class AIInvalidOutput(AIServiceError):
    code = "AI_INVALID_OUTPUT"
    message = "The AI returned an unusable response."


class PromptTooLarge(NyayaError):
    code = "PROMPT_TOO_LARGE"
    message = "The request is too large to process. Please shorten it."


@dataclass
class ProviderResult:
    data: dict
    prompt_version: str


@dataclass
class CallStats:
    llm_calls: int = 0
    cache_hits: int = 0
    prompt_versions: Dict[str, str] = field(default_factory=dict)


def extract_json(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?", "", text or "").replace("```", "").strip()
    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not m:
            raise AIInvalidOutput()
        try:
            obj = json.loads(m.group())
        except json.JSONDecodeError as exc:
            raise AIInvalidOutput() from exc
    if not isinstance(obj, dict):
        raise AIInvalidOutput()
    return obj


class EmbeddingProvider(ABC):
    name = "base"
    dimensions = settings.EMBEDDING_DIM

    @abstractmethod
    def embed_texts(self, texts: List[str], *, query: bool = False) -> List[List[float]]:
        ...


class AIProviderInterface(ABC):
    """High-level legal-AI operations. Every method returns a ProviderResult whose data is UNTRUSTED
    until validated by the schemas in ai.schemas."""
    name = "base"
    model = ""

    def __init__(self):
        self.stats = CallStats()

    @abstractmethod
    def analyze_intake(self, user_text: str, topics: List[str]) -> ProviderResult: ...

    @abstractmethod
    def rewrite_query(self, summary: str, topic: str, issues: List[str]) -> ProviderResult: ...

    @abstractmethod
    def generate_answer(self, question: str, language: str, context: str, passages: List[dict]) -> ProviderResult: ...

    @abstractmethod
    def summarize_judgment(self, question: str, language: str, passages: List[dict]) -> ProviderResult: ...

    @abstractmethod
    def analyze_document(self, language: str, passages: List[dict]) -> ProviderResult: ...

    @abstractmethod
    def generate_action_plan(self, language: str, facts: str, unknowns: str, passages: List[dict],
                             topic: str = "OTHER", flags: Optional[List[str]] = None) -> ProviderResult: ...

    # convenience wrappers required by the architecture spec
    def classify(self, text: str, topics: List[str]) -> str:
        return str(self.analyze_intake(text, topics).data.get("legal_topic", "OTHER"))

    def extract_entities(self, text: str, topics: List[str]) -> dict:
        d = self.analyze_intake(text, topics).data
        return {k: d.get(k) for k in ("state", "district", "court", "case_number", "cnr", "documents")}


def format_sources(passages: List[dict], limit: int) -> str:
    out = []
    for p in passages:
        meta = " | ".join(x for x in [p.get("title"), p.get("citation"), p.get("locator")] if x)
        out.append(f"[{p['label']}] {meta}\n{(p.get('text') or '')[:limit]}")
    return "\n\n".join(out) or "(no sources retrieved)"


class LLMProvider(AIProviderInterface):
    """Template: subclasses implement only `_complete`. Prompts come from the versioned prompt files."""
    cache_enabled = True

    @abstractmethod
    def _complete(self, prompt: str, max_tokens: int) -> str: ...

    def _json_call(self, ref: str, **variables) -> ProviderResult:
        prompt, version = render(ref, **variables)
        if len(prompt) > settings.AI_MAX_PROMPT_CHARS:
            raise PromptTooLarge()
        self.stats.prompt_versions[ref.split("/")[1]] = version
        key = "ai:" + hashlib.sha256(f"{self.name}:{self.model}:{prompt}".encode()).hexdigest()
        if self.cache_enabled:
            hit = cache.get(key)
            if hit is not None:
                self.stats.cache_hits += 1
                return ProviderResult(hit, version)
        self.stats.llm_calls += 1
        data = extract_json(self._complete(prompt, settings.AI_MAX_OUTPUT_TOKENS))
        if self.cache_enabled:
            cache.set(key, data, settings.AI_CACHE_TTL_SECONDS)
        return ProviderResult(data, version)

    def analyze_intake(self, user_text, topics):
        return self._json_call("intake/intake", user_text=user_text, topics=json.dumps(topics))

    def rewrite_query(self, summary, topic, issues):
        return self._json_call("research/query_rewrite", summary=summary, topic=topic, issues="; ".join(issues))

    def generate_answer(self, question, language, context, passages):
        return self._json_call("research/grounded_answer", question=question, language=language, context=context,
                               sources=format_sources(passages, settings.RETRIEVAL_PASSAGE_CHARS))

    def summarize_judgment(self, question, language, passages):
        return self._json_call("explanation/judgment_explain", question=question or "", language=language,
                               sources=format_sources(passages, settings.RETRIEVAL_PASSAGE_CHARS))

    def analyze_document(self, language, passages):
        return self._json_call("explanation/document_analyze", language=language,
                               sources=format_sources(passages, settings.RETRIEVAL_PASSAGE_CHARS))

    def generate_action_plan(self, language, facts, unknowns, passages, topic="OTHER", flags=None):
        return self._json_call("action_plan/action_plan", language=language, facts=facts, unknowns=unknowns,
                               sources=format_sources(passages, settings.RETRIEVAL_PASSAGE_CHARS))
