"""CitationVerificationService: nothing the model cites reaches the user unless it matches a stored source.

Checks (1) [S#] labels point at passages actually retrieved for this request, (2) any free-text legal citation
(e.g. "AIR 1990 SC 867") exists in the database, (3) any "A v. B" case name matches a stored judgment title.
Unverifiable references are redacted from the text and reported; fewer verified sources beat many uncertain ones.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from django.db.models import F, Func, Value
from django.db.models.functions import Lower

from ai.services.retrieval_context import Evidence, EvidenceSet
from judgments.models import Judgment
from sources.models import Source

LABEL_RE = re.compile(r"\[(S\d+)\]")
CITATION_PATTERNS = [
    re.compile(r"\bAIR\s+\d{4}\s+[A-Z][A-Za-z]{1,10}\s+\d{1,5}\b"),
    re.compile(r"\(\d{4}\)\s+\d{1,3}\s+[A-Z][A-Za-z]{1,6}\s+\d{1,5}\b"),
    re.compile(r"\b\d{4}\s+\(\d{1,3}\)\s+[A-Z][A-Za-z]{1,6}\s+\d{1,5}\b"),
    re.compile(r"\b\d{4}\s+SCC\s+OnLine\s+[A-Za-z]{2,10}\s+\d{1,6}\b"),
    re.compile(r"\[\d{4}\]\s+\d{1,3}\s+[A-Z]{2,6}\s+\d{1,5}\b"),
]
_PARTY = r"[A-Z][\w.&'’\-]*(?:\s+(?:of|the|and|&|[A-Z][\w.&'’\-]*)){0,6}"
CASE_NAME_RE = re.compile(rf"\b({_PARTY})\s+v(?:s)?\.?\s+({_PARTY})")
REDACTED = {"en": "[unverified reference removed]", "hi": "[असत्यापित संदर्भ हटाया गया]"}


def norm(s: str) -> str:
    return re.sub(r"[\s.,()\[\]]", "", (s or "")).lower()


@dataclass
class VerificationReport:
    answer: str
    sources: List[dict] = field(default_factory=list)
    rejected: List[dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    status: str = "no_sources"
    cited_labels: List[str] = field(default_factory=list)


class CitationVerificationService:
    def _citation_in_db(self, citation: str) -> Optional[Judgment]:
        n = norm(citation)
        expr = Lower(Func(F("citation"), Value(r"[\s.,()\[\]]"), Value(""), Value("g"), function="REGEXP_REPLACE"))
        return (Judgment.objects.filter(citation__isnull=False).annotate(_n=expr).filter(_n=n).first())

    def _name_in_db(self, a: str, b: str, evidence: EvidenceSet) -> bool:
        words = lambda s: [w for w in re.findall(r"[A-Za-z]{4,}", s.lower()) if w not in {"state", "union", "india", "others"}] or re.findall(r"[A-Za-z]{3,}", s.lower())  # noqa: E731
        wa, wb = words(a), words(b)
        if not wa or not wb:
            return False
        titles = [e.title.lower() for e in evidence.items.values()]
        for t in titles:
            if wa[0] in t and wb[0] in t:
                return True
        return Judgment.objects.filter(title__icontains=wa[0]).filter(title__icontains=wb[0]).exists()

    def verify(self, answer: str, evidence: EvidenceSet, lang: str = "en", extra_texts: Optional[List[str]] = None,
               claim_labels: Optional[List[str]] = None) -> VerificationReport:
        rep = VerificationReport(answer=answer or "")
        red = REDACTED["hi" if lang == "hi" else "en"]
        valid = set(evidence.items)
        text = rep.answer

        # 1. labels
        used: List[str] = []
        for lab in LABEL_RE.findall(text):
            if lab in valid:
                if lab not in used:
                    used.append(lab)
            else:
                rep.rejected.append({"type": "LABEL", "value": lab, "reason": "Label does not match any retrieved source"})
        text = LABEL_RE.sub(lambda m: m.group(0) if m.group(1) in valid else "", text)
        for lab in (claim_labels or []):
            if lab in valid and lab not in used:
                used.append(lab)

        # 2. free-text citations (answer + any extra text such as next steps)
        blob_allowed = norm(evidence.text_blob())
        matched_db: List[Judgment] = []
        for pat in CITATION_PATTERNS:
            for m in set(pat.findall(text)):
                if norm(m) in blob_allowed:
                    continue                                   # appears in a retrieved passage / source
                j = self._citation_in_db(m)
                if j is not None:
                    matched_db.append(j)
                else:
                    rep.rejected.append({"type": "CITATION", "value": m, "reason": "Citation not found in stored sources"})
                    text = text.replace(m, red)

        # 3. case names
        for m in CASE_NAME_RE.finditer(text):
            a, b = m.group(1), m.group(2)
            if not self._name_in_db(a, b, evidence):
                rep.rejected.append({"type": "CASE_NAME", "value": m.group(0), "reason": "Case name not found in stored sources"})
                text = text.replace(m.group(0), red)

        rep.answer = text
        rep.cited_labels = used

        # 4. attach verified source references (cited first, then other retrieved ones flagged as not cited)
        for lab, e in evidence.items.items():
            rep.sources.append(e.as_source_dict(cited=lab in used))
        seen = {s["source_id"] for s in rep.sources}
        for j in matched_db:
            if j.source_id and str(j.source_id) not in seen:
                src: Source = j.source
                rep.sources.append({"label": None, "source_id": str(src.id), "judgment_id": str(j.id), "title": j.title,
                                    "citation": j.citation, "court": j.court.name if j.court else None,
                                    "date": j.judgment_date.isoformat() if j.judgment_date else None,
                                    "source_type": src.source_type, "source_url": j.source_url or src.url, "locator": None,
                                    "verification_status": src.verification_status, "is_demo_data": src.is_demo_data,
                                    "retrieved_at": src.retrieved_at.isoformat(), "relevance_score": None,
                                    "relevance_reason": None, "document_id": None, "page_number": None, "cited": True})
        rep.sources.sort(key=lambda s: (not s["cited"],))
        cited = [s for s in rep.sources if s["cited"]]

        # 5. status
        if not rep.sources:
            rep.status = "no_sources"
        elif not cited:
            rep.status = "unverified"
            rep.warnings.append("Sources were retrieved but the answer did not cite them; treat the answer as unverified.")
        elif any(s["is_demo_data"] for s in cited):
            rep.status = "demo_data"
        elif rep.rejected:
            rep.status = "partially_verified"
        elif all(s["verification_status"] == "VERIFIED" for s in cited):
            rep.status = "verified"
        else:
            rep.status = "unverified"
        if rep.rejected:
            rep.warnings.append("Some references in the generated text could not be verified and were removed.")
        return rep

    @staticmethod
    def persist(response, report: VerificationReport):
        """Store citation rows for an AIResponse (verified sources + rejected attempts)."""
        from ai.models import Citation, CitationStatus
        rows = []
        for s in report.sources:
            if s["cited"]:
                rows.append(Citation(response=response, source_id=s["source_id"],
                                     label=s["label"] or "DB", locator=s.get("locator"), status=CitationStatus.VERIFIED,
                                     snapshot={"title": s["title"], "citation": s["citation"], "court": s["court"]}))
        for r in report.rejected:
            rows.append(Citation(response=response, label=r["type"][:20], status=CitationStatus.REJECTED,
                                 snapshot={"value": r["value"], "reason": r["reason"]}))
        Citation.objects.bulk_create(rows)
