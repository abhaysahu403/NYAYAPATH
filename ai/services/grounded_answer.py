"""GroundedAnswerService: answer ONLY from retrieved passages. No passages -> no LLM call, honest "not found"."""
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from pydantic import ValidationError

from ai.providers.factory import get_ai_provider
from ai.schemas import Claim, GroundedAnswer, NextStep
from ai.services.retrieval_context import EvidenceSet
from core.exceptions import NyayaError

logger = logging.getLogger("nyayapath.ai.answer")
LABEL_RE = re.compile(r"\[(S\d+)\]")

NOT_FOUND = {
    "en": "No relevant verified sources were found for your question in the available data. Adding details such as state, district or case number may improve the search.",
    "hi": "उपलब्ध सत्यापित स्रोतों में आपके प्रश्न से संबंधित जानकारी नहीं मिली। राज्य, जिला या केस नंबर जैसे विवरण देने से खोज बेहतर हो सकती है।",
}


@dataclass
class AnswerDraft:
    answer: str
    claims: List[Claim] = field(default_factory=list)
    next_steps: List[NextStep] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    llm_used: bool = False
    degraded: bool = False


def _first(text: str, n=2, limit=350) -> str:
    return " ".join(re.split(r"(?<=[.!?।])\s+", (text or "").strip())[:n])[:limit].rstrip()


def extractive_answer(evidence: EvidenceSet, lang: str) -> AnswerDraft:
    """Deterministic fallback: quote what the retrieved sources say, with labels. No model involved."""
    hi = lang == "hi"
    claims, lines = [], []
    for e in list(evidence.items.values())[:3]:
        s = _first(e.text)
        claims.append(Claim(text=s, kind="SOURCE_INFO", source_ids=[e.label]))
        lines.append(f"- {s} [{e.label}]")
    lead = ("उपलब्ध जानकारी के आधार पर, प्राप्त स्रोतों में निम्न प्रासंगिक जानकारी मिली (स्रोत मूल भाषा में हैं):" if hi
            else "Based on the available information, the retrieved sources contain the following relevant points:")
    return AnswerDraft(answer="\n".join([lead, *lines]), claims=claims, degraded=True)


class GroundedAnswerService:
    def __init__(self, provider=None):
        self._provider = provider

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_ai_provider()
        return self._provider

    def answer(self, question: str, language: str, context: str, evidence: EvidenceSet) -> AnswerDraft:
        if not evidence:
            return AnswerDraft(answer=NOT_FOUND["hi" if language == "hi" else "en"],
                               unknowns=["No matching verified source in the indexed corpus"])
        try:
            raw = self.provider.generate_answer(question, language, context, evidence.passages()).data
            parsed = GroundedAnswer.model_validate(raw)
        except (NyayaError, ValidationError, TypeError, AttributeError):
            logger.warning("grounded_answer_fallback", extra={"service": "grounded_answer"})
            return extractive_answer(evidence, language)
        valid = set(evidence.items)
        claims: List[Claim] = []
        for c in parsed.claims:
            ids = [s for s in c.source_ids if s in valid]
            if c.kind == "SOURCE_INFO" and not ids:
                continue                       # a "source says" claim with no real source is dropped
            claims.append(Claim(text=c.text, kind=c.kind, source_ids=ids))
        steps = [NextStep(title=s.title, detail=s.detail, source_ids=[i for i in s.source_ids if i in valid])
                 for s in parsed.next_steps]
        return AnswerDraft(answer=parsed.answer.strip(), claims=claims, next_steps=steps, unknowns=parsed.unknowns,
                           llm_used=True)
