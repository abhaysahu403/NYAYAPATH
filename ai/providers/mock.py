"""Deterministic offline providers used by tests and local development (no external calls).

MockAIProvider is NOT an LLM: it uses heuristics + extractive answers built from retrieved passages. Responses
are labelled with provider="mock" so a frontend can show a development banner.
"""
import hashlib
import math
import re
from typing import List, Optional

from ai.providers.base import AIProviderInterface, EmbeddingProvider, ProviderResult
from ai.services import heuristics, playbooks
from ai.services.language import detect_language

_TOKEN = re.compile(r"[\w\u0900-\u097F]+", re.UNICODE)
_STOP = {"the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "is", "are", "was", "be", "by", "with", "that",
         "this", "it", "as", "at", "from", "which", "not", "may", "can", "if", "has", "have", "had"}


class HashingEmbeddingProvider(EmbeddingProvider):
    """Feature-hashing bag-of-words embedding: deterministic, offline, lexically meaningful (NOT semantic)."""
    name = "mock-hash"

    def _vec(self, text: str) -> List[float]:
        v = [0.0] * self.dimensions
        toks = [t.lower() for t in _TOKEN.findall(text or "") if t.lower() not in _STOP and len(t) > 1]
        for t in toks:
            h = int(hashlib.md5(t.encode()).hexdigest(), 16)
            v[h % self.dimensions] += 1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def embed_texts(self, texts, *, query=False):
        return [self._vec(t) for t in texts]


def _first_sentences(text: str, n: int = 2, limit: int = 350) -> str:
    parts = re.split(r"(?<=[.!?।])\s+", (text or "").strip())
    out = " ".join(parts[:n]).strip()
    return out[:limit].rstrip()


class MockAIProvider(AIProviderInterface):
    name = "mock"
    model = "mock-heuristic-v1"

    def _res(self, data, ref):
        self.stats.prompt_versions[ref] = f"mock/{ref}_v1"
        return ProviderResult(data, f"mock/{ref}_v1")

    def analyze_intake(self, user_text, topics):
        d = heuristics.analyse(user_text)
        return self._res(d, "intake")

    def rewrite_query(self, summary, topic, issues):
        kws = heuristics.expand_keywords(summary) or [w for w in re.findall(r"[A-Za-z]{4,}", summary)][:6]
        base = " ".join(kws[:6])
        return self._res({"queries": [q for q in [base, f"{topic.lower().replace('_', ' ')} {base}".strip()] if q.strip()],
                          "keywords": kws}, "query_rewrite")

    def generate_answer(self, question, language, context, passages):
        hi = language == "hi"
        claims, steps = [], []
        for p in passages[:3]:
            snippet = _first_sentences(p.get("text", ""))
            claims.append({"text": snippet, "kind": "SOURCE_INFO", "source_ids": [p["label"]]})
        if passages:
            lead = ("उपलब्ध जानकारी के आधार पर, प्राप्त स्रोतों में निम्न प्रासंगिक जानकारी मिली (स्रोत मूल भाषा में हैं):"
                    if hi else "Based on the available information, the retrieved sources contain the following relevant points:")
            lines = [f"- {c['text']} [{c['source_ids'][0]}]" for c in claims]
            tail = ("यह केवल कानूनी जानकारी है; दाखिल करने से पहले किसी योग्य वकील से सत्यापित करें।"
                    if hi else "This is legal information only; verify with a qualified legal professional before filing.")
            answer = "\n".join([lead, *lines, tail])
            claims.append({"text": ("ये स्रोत आपकी समस्या से संबंधित प्रतीत होते हैं, पर यह नहीं कहा जा सकता कि वे आपके मामले पर लागू होंगे।"
                                    if hi else "These sources appear related to your problem, but it cannot be said that they apply to your specific case."),
                           "kind": "INTERPRETATION", "source_ids": []})
        else:
            answer = ("उपलब्ध सत्यापित स्रोतों में आपके प्रश्न से संबंधित जानकारी नहीं मिली। अधिक विवरण (राज्य, जिला, केस नंबर) देने पर खोज बेहतर हो सकती है।"
                      if hi else "No relevant verified sources were found for your question in the available data. More details (state, district, case number) may improve the search.")
        unknowns = []
        if "case_number" in context and "unknown" in context.lower():
            unknowns.append("Case number / CNR not provided")
        return self._res({"answer": answer, "claims": claims, "next_steps": steps, "unknowns": unknowns}, "grounded_answer")

    def summarize_judgment(self, question, language, passages):
        text = " ".join(p.get("text", "") for p in passages)
        labels = [p["label"] for p in passages[:3]]
        return self._res({"plain_summary": _first_sentences(text, 3, 700) or "No text available.", "key_facts": [],
                          "legal_issue": None, "court_reasoning": None, "outcome": None,
                          "relevance_to_question": None, "source_ids": labels}, "judgment_explain")

    def analyze_document(self, language, passages):
        text = " ".join(p.get("text", "") for p in passages)
        dates = re.findall(r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b", text)[:8]
        return self._res({"document_type": None, "plain_summary": _first_sentences(text, 3, 700) or "No readable text.",
                          "key_facts": [], "important_dates": dates, "parties": [],
                          "suggested_questions": ["What is the current stage of this matter?", "What are my options and their risks?"],
                          "source_ids": [p["label"] for p in passages[:2]]}, "document_analyze")

    def generate_action_plan(self, language, facts, unknowns, passages, topic="OTHER", flags: Optional[List[str]] = None):
        has_case = "existing_case: True" in facts
        keys = playbooks.select_steps(topic, flags or [], has_case)
        by_key = {}
        for p in passages:
            if p.get("key"):
                by_key[p["key"]] = p["label"]
        steps = []
        for k in keys:
            b = playbooks.build(k, language)
            ids = [by_key[x] for x in b["keys"] if x in by_key]
            steps.append({"title": b["title"], "description": b["description"], "why_relevant": b["why_relevant"],
                          "required_documents": b["required_documents"], "legal_basis": None, "estimated_timeline": None,
                          "difficulty": b["difficulty"], "kind": b["kind"], "source_ids": ids})
        hi = language == "hi"
        return self._res({
            "title": "संभावित अगले कदम" if hi else "Possible next steps",
            "situation_assessment": ("उपलब्ध जानकारी के आधार पर, नीचे दिए गए कदम केवल संभावित विकल्प हैं और इन्हें किसी योग्य वकील से सत्यापित करना चाहिए।"
                                     if hi else "Based on the available information, the steps below are possible options to discuss and verify with a qualified legal professional."),
            "delay_cause_analysis": None,
            "immediate_priority": ("अपने दस्तावेज़ इकट्ठा करना और केस की वर्तमान स्थिति की पुष्टि करना उपयोगी प्रारंभिक कदम हो सकता है।"
                                   if hi else "Collecting your documents and confirming the current case status may be a useful first step."),
            "steps": steps,
            "warnings": [("यह कानूनी सलाह नहीं है। किसी भी परिणाम की गारंटी नहीं दी जा सकती।" if hi else "This is not legal advice. No outcome can be guaranteed.")],
        }, "action_plan")
