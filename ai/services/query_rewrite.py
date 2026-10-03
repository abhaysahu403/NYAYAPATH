"""QueryRewriteService: citizen problem -> English search queries + keywords for the (mostly English) corpus."""
import logging
from typing import List, Optional

from pydantic import ValidationError

from ai.providers.factory import get_ai_provider
from ai.schemas import IntakeResult, QueryRewrite
from ai.services import heuristics
from core.exceptions import NyayaError

logger = logging.getLogger("nyayapath.ai.rewrite")


def _dedupe(items: List[str], limit: int) -> List[str]:
    out: List[str] = []
    for i in items:
        i = (i or "").strip()
        if i and i.lower() not in {o.lower() for o in out}:
            out.append(i)
    return out[:limit]


class QueryRewriteService:
    def __init__(self, provider=None):
        self._provider = provider

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_ai_provider()
        return self._provider

    def rewrite(self, intake: IntakeResult, text: str) -> QueryRewrite:
        summary = (intake.problem_summary_en or text or "")[:1500]
        topic = intake.legal_topic
        # Deterministic keywords always included: they translate Hindi/Hinglish terms reliably.
        det_kw = heuristics.expand_keywords(text or "") + heuristics.expand_keywords(summary)
        llm_queries: List[str] = []
        llm_kw: List[str] = []
        try:
            raw = self.provider.rewrite_query(summary, topic, intake.key_issues).data
            raw = {"queries": list(raw.get("queries") or [])[:5], "keywords": list(raw.get("keywords") or [])[:12]}
            parsed = QueryRewrite.model_validate(raw)
            llm_queries, llm_kw = parsed.queries, parsed.keywords
        except (NyayaError, ValidationError, TypeError, AttributeError):
            logger.warning("query_rewrite_fallback", extra={"service": "query_rewrite"})
        keywords = _dedupe(list(intake.search_keywords) + llm_kw + det_kw, 12)
        queries = _dedupe([q for q in llm_queries if q], 4)
        if not queries:
            base = " ".join(keywords[:8]) or (intake.problem_summary_en or "")
            if base:
                queries.append(base)
            if topic != "OTHER" and base:
                queries.append(f"{topic.lower().replace('_', ' ')} {base}"[:200])
        return QueryRewrite(queries=_dedupe(queries, 4), keywords=keywords)
