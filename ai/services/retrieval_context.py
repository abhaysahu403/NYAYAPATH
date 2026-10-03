"""Turns search hits into labelled passages (S1, S2, ...) the LLM may cite, and keeps the label->evidence map."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from django.conf import settings


@dataclass
class Evidence:
    label: str
    source_id: Optional[str]
    title: str
    text: str
    citation: Optional[str] = None
    locator: Optional[str] = None
    court: Optional[str] = None
    date: Optional[str] = None
    source_type: Optional[str] = None
    url: Optional[str] = None
    verification_status: Optional[str] = None
    is_demo: bool = False
    judgment_id: Optional[str] = None
    key: Optional[str] = None
    retrieved_at: Optional[str] = None
    relevance: Optional[float] = None
    relevance_reason: Optional[str] = None
    document_id: Optional[str] = None
    page_number: Optional[int] = None

    def as_passage(self) -> dict:
        return {"label": self.label, "title": self.title, "citation": self.citation, "locator": self.locator,
                "text": self.text, "key": self.key}

    def as_source_dict(self, cited: bool = True) -> dict:
        return {"label": self.label, "source_id": self.source_id, "judgment_id": self.judgment_id, "title": self.title,
                "citation": self.citation, "court": self.court, "date": self.date, "source_type": self.source_type,
                "source_url": self.url, "locator": self.locator, "verification_status": self.verification_status,
                "is_demo_data": self.is_demo, "retrieved_at": self.retrieved_at, "relevance_score": self.relevance,
                "relevance_reason": self.relevance_reason, "document_id": self.document_id,
                "page_number": self.page_number, "cited": cited}


@dataclass
class EvidenceSet:
    items: Dict[str, Evidence] = field(default_factory=dict)

    def passages(self) -> List[dict]:
        return [e.as_passage() for e in self.items.values()]

    def text_blob(self) -> str:
        return "\n".join(f"{e.title}\n{e.citation or ''}\n{e.text}" for e in self.items.values())

    def __bool__(self):
        return bool(self.items)


def _locator(chunk) -> Optional[str]:
    if chunk.section_title:
        return chunk.section_title
    return f"p. {chunk.page_number}" if chunk.page_number else None


def evidence_from_hits(hits, lang: str = "en") -> EvidenceSet:
    from legal_research.services.research import hit_to_dict
    from legal_research.services.search import SearchFilters
    es = EvidenceSet()
    for i, h in enumerate(hits, 1):
        d = hit_to_dict(h, SearchFilters(), lang)
        label = f"S{i}"
        es.items[label] = Evidence(
            label=label, source_id=d["source_id"], judgment_id=d["judgment_id"], title=d["title"],
            text=h.chunk.text[: settings.RETRIEVAL_PASSAGE_CHARS], citation=d["citation"], locator=d["locator"],
            court=d["court"], date=d["date"], source_type=d["source_type"], url=d["source_url"],
            verification_status=d["verification_status"], is_demo=d["is_demo_data"],
            key=(h.source.metadata or {}).get("key"), retrieved_at=d["retrieved_at"], relevance=d["relevance_score"],
            relevance_reason=d["relevance_reason"])
    return es


def evidence_from_document_chunks(chunks) -> EvidenceSet:
    es = EvidenceSet()
    for i, c in enumerate(chunks, 1):
        label = f"S{i}"
        doc = c.document
        loc = " – ".join(x for x in [f"p. {c.page_number}" if c.page_number else None, c.section_title] if x) or None
        es.items[label] = Evidence(
            label=label, source_id=str(doc.source_id) if doc.source_id else None, title=doc.original_filename,
            text=c.text[: settings.RETRIEVAL_PASSAGE_CHARS], locator=loc, source_type="USER_DOCUMENT",
            verification_status="UNVERIFIED", document_id=str(doc.id), page_number=c.page_number)
    return es
