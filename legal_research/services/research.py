from dataclasses import dataclass, field
from typing import List, Optional

from django.conf import settings

from ai.schemas import IntakeResult
from ai.services.query_rewrite import QueryRewriteService
from legal_research.models import ResearchResult, SearchKind, SearchQuery
from legal_research.services.search import Hit, HybridSearchService, SearchFilters, reason_text

SIMILARITY_NOTE = {
    "en": "Similarity means semantically similar according to the indexed corpus. It does NOT mean the cases are legally identical or that the same outcome would follow.",
    "hi": "समानता का अर्थ है अनुक्रमित स्रोतों के अनुसार अर्थ-संबंधी समानता। इसका अर्थ यह नहीं कि मामले कानूनी रूप से समान हैं या परिणाम भी वही होगा।",
}


@dataclass
class ResearchOutcome:
    hits: List[Hit] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    filters: Optional[SearchFilters] = None


def hit_to_dict(hit: Hit, filters: SearchFilters, lang: str = "en") -> dict:
    src, j = hit.source, hit.judgment
    return {
        "source_id": str(src.id),
        "judgment_id": str(j.id) if j else None,
        "title": j.title if j else src.title,
        "court": (j.court.name if j and j.court else src.court),
        "date": (j.judgment_date.isoformat() if j and j.judgment_date else (src.publication_date.isoformat() if src.publication_date else None)),
        "citation": j.citation if j else (src.identifier if src.source_type == "JUDGMENT" else None),
        "source_type": src.source_type,
        "relevance_score": hit.relevance,
        "relevance_label": hit.label,
        "relevance_reason": reason_text(hit, filters, lang),
        "source_url": (j.source_url if j and j.source_url else src.url),
        "snippet": hit.chunk.text[:400],
        "locator": hit.chunk.section_title or (f"p. {hit.chunk.page_number}" if hit.chunk.page_number else None),
        "verification_status": src.verification_status,
        "is_demo_data": src.is_demo_data,
        "retrieved_at": src.retrieved_at.isoformat() if src.retrieved_at else None,
    }


class LegalResearchService:
    """Citizen problem -> search queries -> hybrid retrieval -> ranked, explained sources."""

    def __init__(self, provider=None, embedder=None):
        self.rewriter = QueryRewriteService(provider)
        self.search_service = HybridSearchService(embedder)

    def research(self, intake: IntakeResult, text: str, filters: Optional[SearchFilters] = None,
                 top_k: Optional[int] = None, judgments_only: bool = False) -> ResearchOutcome:
        f = filters or SearchFilters()
        if not f.state and intake.state:
            f.state = intake.state
        f.judgments_only = judgments_only or f.judgments_only
        plan = self.rewriter.rewrite(intake, text)
        hits = self.search_service.search(plan.queries, plan.keywords, f, top_k or settings.RETRIEVAL_TOP_K,
                                          inferred_topic=intake.legal_topic if intake.legal_topic != "OTHER" else None)
        return ResearchOutcome(hits=hits, queries=plan.queries, keywords=plan.keywords, filters=f)

    @staticmethod
    def record(user, kind: str, query_text: str, outcome: ResearchOutcome, lang: str = "en") -> SearchQuery:
        sq = SearchQuery.objects.create(
            user=user if user and user.is_authenticated else None, kind=kind, query_text=query_text[:2000],
            rewritten_queries=outcome.queries, filters=outcome.filters.as_dict() if outcome.filters else {},
            language=lang, result_count=len(outcome.hits))
        ResearchResult.objects.bulk_create([
            ResearchResult(search_query=sq, source=h.source, judgment=h.judgment, rank=i, relevance_score=h.relevance,
                           relevance_reason=reason_text(h, outcome.filters or SearchFilters(), lang))
            for i, h in enumerate(outcome.hits, 1)])
        return sq
