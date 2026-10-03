"""Hybrid retrieval: pgvector semantic search + Postgres full-text + metadata filters, fused with
Reciprocal Rank Fusion (RRF). Private user documents are NEVER part of public research."""
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F, Q
from pgvector.django import CosineDistance

from ai.embedding import EmbeddingService
from ai.providers.mock import _STOP
from legal_research.models import KnowledgeChunk
from sources.models import SourceType, VerificationStatus

RRF_K = 60
CANDIDATES = 40
SEMANTIC_MAX_DISTANCE = 0.85
_TOKEN = re.compile(r"[\w\u0900-\u097F]{3,}", re.UNICODE)


@dataclass
class SearchFilters:
    state: Optional[str] = None
    court: Optional[str] = None
    district: Optional[str] = None
    topic: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    language: Optional[str] = None
    source_type: Optional[str] = None
    judgments_only: bool = False

    def as_dict(self) -> dict:
        return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in self.__dict__.items() if v not in (None, "", False)}


@dataclass
class Hit:
    chunk: KnowledgeChunk
    score: float = 0.0           # RRF score (internal)
    relevance: float = 0.0       # normalised 0..1 within this result set (NOT legal certainty)
    signals: List[str] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)

    @property
    def source(self):
        return self.chunk.source

    @property
    def judgment(self):
        return self.chunk.judgment

    @property
    def label(self) -> str:
        n = len(self.signals)
        return "STRONG" if n >= 3 else "MODERATE" if n == 2 else "WEAK"


def _terms(texts: List[str], keywords: List[str]) -> List[str]:
    out: List[str] = []
    for t in list(keywords) + list(texts):
        for tok in _TOKEN.findall(t.lower()):
            if tok not in _STOP and tok not in out:
                out.append(tok)
    return out[:25]


def reason_text(hit: Hit, filters: SearchFilters, lang: str = "en") -> str:
    """Deterministic explanation built only from measurable matches (never LLM-written)."""
    parts = []
    hi = lang == "hi"
    if hit.matched_keywords:
        kws = ", ".join(hit.matched_keywords[:5])
        parts.append(f"मेल खाने वाले शब्द: {kws}" if hi else f"Matching terms: {kws}")
    if "TOPIC" in hit.signals:
        parts.append("विषय मेल खाता है" if hi else "Legal topic matches")
    if "STATE" in hit.signals:
        parts.append(f"राज्य मेल खाता है: {hit.chunk.state}" if hi else f"Same state: {hit.chunk.state}")
    if "SEMANTIC" in hit.signals:
        parts.append("अनुक्रमित स्रोतों में आपके विवरण से अर्थ-संबंधी समानता" if hi else "Semantically similar to your description within the indexed corpus")
    return "; ".join(parts) or ("सीमित मिलान" if hi else "Limited match")


class HybridSearchService:
    def __init__(self, embedder: Optional[EmbeddingService] = None):
        self.embedder = embedder or EmbeddingService()

    # ---- candidate set (metadata filtering) ----
    def candidate_queryset(self, f: SearchFilters):
        qs = (KnowledgeChunk.objects.select_related("source", "judgment", "judgment__court")
              .exclude(source__source_type=SourceType.USER_DOCUMENT)
              .filter(Q(source__verification_status=VerificationStatus.VERIFIED) | Q(source__is_demo_data=True)))
        if f.judgments_only:
            qs = qs.filter(judgment__isnull=False)
        if f.state:  # national sources (state is null, e.g. Supreme Court / central law) stay eligible
            qs = qs.filter(Q(state__iexact=f.state) | Q(state__isnull=True) | Q(state=""))
        if f.court:
            qs = qs.filter(judgment__court__name__icontains=f.court)
        if f.district:
            qs = qs.filter(judgment__district__iexact=f.district)
        if f.topic:
            qs = qs.filter(topics__contains=[f.topic])
        if f.date_from:
            qs = qs.filter(judgment__judgment_date__gte=f.date_from)
        if f.date_to:
            qs = qs.filter(judgment__judgment_date__lte=f.date_to)
        if f.language:
            qs = qs.filter(language=f.language)
        if f.source_type:
            qs = qs.filter(source__source_type=f.source_type)
        return qs

    def search(self, queries: List[str], keywords: List[str], filters: SearchFilters, top_k: int = 5,
               inferred_topic: Optional[str] = None, hard_cap: Optional[int] = None) -> List[Hit]:
        top_k = max(1, min(top_k, hard_cap or settings.RETRIEVAL_MAX_TOP_K))
        base = self.candidate_queryset(filters)
        text = " ".join(q for q in queries if q).strip()
        terms = _terms(queries, keywords)
        if not text and not terms:
            return []

        scores: Dict = {}
        signals: Dict = {}
        chunks: Dict = {}

        # semantic
        qvec = self.embedder.embed_query(text or " ".join(terms))
        sem = (base.filter(embedding__isnull=False).annotate(dist=CosineDistance("embedding", qvec))
               .filter(dist__lte=SEMANTIC_MAX_DISTANCE).order_by("dist")[:CANDIDATES])
        for rank, ch in enumerate(sem, 1):
            scores[ch.pk] = scores.get(ch.pk, 0) + 1 / (RRF_K + rank)
            signals.setdefault(ch.pk, set()).add("SEMANTIC")
            chunks[ch.pk] = ch

        # keyword (full-text, OR of terms)
        if terms:
            sq = SearchQuery(terms[0], config="simple")
            for t in terms[1:]:
                sq = sq | SearchQuery(t, config="simple")
            vec = SearchVector("text", config="simple")
            kw = (base.annotate(_sv=vec).filter(_sv=sq).annotate(_rank=SearchRank(vec, sq)).order_by("-_rank")[:CANDIDATES])
            for rank, ch in enumerate(kw, 1):
                scores[ch.pk] = scores.get(ch.pk, 0) + 1 / (RRF_K + rank)
                signals.setdefault(ch.pk, set()).add("KEYWORD")
                chunks[ch.pk] = ch

        # metadata boosts
        want_topic = filters.topic or inferred_topic
        for pk, ch in chunks.items():
            if want_topic and want_topic in (ch.topics or []):
                scores[pk] *= 1.25
                signals[pk].add("TOPIC")
            if filters.state and ch.state and ch.state.lower() == filters.state.lower():
                scores[pk] *= 1.15
                signals[pk].add("STATE")

        # best chunk per source
        best: Dict = {}
        for pk, sc in scores.items():
            sid = chunks[pk].source_id
            if sid not in best or sc > scores[best[sid]]:
                best[sid] = pk
        ranked = sorted(best.values(), key=lambda pk: -scores[pk])[:top_k]
        if not ranked:
            return []
        top = scores[ranked[0]]
        hits = []
        for pk in ranked:
            ch = chunks[pk]
            low = ch.text.lower() + " " + (ch.source.title or "").lower()
            mk = [t for t in terms if t in low][:6]
            h = Hit(chunk=ch, score=scores[pk], relevance=round(scores[pk] / top, 3),
                    signals=sorted(signals[pk]), matched_keywords=mk)
            hits.append(h)
        return hits


def search_document_chunks(owner, question: str, document_ids=None, top_k: int = 5):
    """Hybrid search restricted to the OWNER's own document chunks."""
    from documents.models import DocumentChunk
    qs = DocumentChunk.objects.select_related("document").filter(document__owner=owner)
    if document_ids:
        qs = qs.filter(document_id__in=document_ids)
    terms = _terms([question], [])
    scores: Dict = {}
    chunks: Dict = {}
    qvec = EmbeddingService().embed_query(question)
    for rank, ch in enumerate(qs.filter(embedding__isnull=False).annotate(dist=CosineDistance("embedding", qvec))
                              .filter(dist__lte=SEMANTIC_MAX_DISTANCE).order_by("dist")[:CANDIDATES], 1):
        scores[ch.pk] = scores.get(ch.pk, 0) + 1 / (RRF_K + rank)
        chunks[ch.pk] = ch
    if terms:
        sq = SearchQuery(terms[0], config="simple")
        for t in terms[1:]:
            sq = sq | SearchQuery(t, config="simple")
        vec = SearchVector("text", config="simple")
        for rank, ch in enumerate(qs.annotate(_sv=vec).filter(_sv=sq).annotate(_r=SearchRank(vec, sq)).order_by("-_r")[:CANDIDATES], 1):
            scores[ch.pk] = scores.get(ch.pk, 0) + 1 / (RRF_K + rank)
            chunks[ch.pk] = ch
    ordered = sorted(scores, key=lambda pk: -scores[pk])[:max(1, min(top_k, settings.RETRIEVAL_MAX_TOP_K))]
    return [chunks[pk] for pk in ordered]
