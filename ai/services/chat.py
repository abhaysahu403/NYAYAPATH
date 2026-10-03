"""ChatOrchestrator: the end-to-end citizen pipeline.

 message -> language/intake -> follow-up questions -> query rewrite -> hybrid retrieval -> grounded answer
 -> citation verification -> safety layer -> structured, source-rich response (+ audit trail in AIRequest/AIResponse)

Every stage is a separate service; this class only wires them together and assembles the response object.
"""
import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.db.models import Q

from ai.models import AIRequestType, Conversation, ConversationMessage, MessageRole
from ai.providers.factory import get_ai_provider
from ai.services import playbooks
from ai.services.citation_verification import CitationVerificationService
from ai.services.followup import FollowUpService
from ai.services.grounded_answer import GroundedAnswerService
from ai.services.intake import LegalIntakeService, intake_to_context
from ai.services.language import response_language
from ai.services.retrieval_context import EvidenceSet, evidence_from_hits
from ai.services.safety import DISCLAIMER, LegalSafetyService
from ai.services.tracking import AICall
from legal_research.models import SearchKind
from legal_research.services.research import LegalResearchService
from legal_research.services.search import SearchFilters

logger = logging.getLogger("nyayapath.ai.chat")

DEMO_NOTICE = {
    "en": "Some sources shown are DEMO data used for development. Do not rely on them as real legal authority.",
    "hi": "दिखाए गए कुछ स्रोत विकास के लिए DEMO डेटा हैं। इन्हें वास्तविक कानूनी प्राधिकार के रूप में न मानें।",
}
CLARIFY = {
    "en": "To understand your situation better, could you tell me a little more?",
    "hi": "आपकी स्थिति को बेहतर समझने के लिए, कृपया थोड़ी और जानकारी दें।",
}


def entities_of(intake) -> dict:
    return {k: getattr(intake, k) for k in ("state", "district", "court", "case_number", "cnr", "existing_case",
                                              "case_age_years", "documents", "property_type", "property_size",
                                              "issue_flags", "urgency")}


def case_references(user, intake, case=None) -> List[dict]:
    """Case records already stored for THIS user that match the identifiers the user mentioned (never fabricated)."""
    from cases.models import Case
    q = Q()
    if intake.cnr:
        q |= Q(cnr_number__iexact=intake.cnr)
    if intake.case_number:
        q |= Q(case_number__iexact=intake.case_number)
    cases = []
    if case is not None:
        cases.append(case)
    elif q and user is not None and getattr(user, "is_authenticated", False):
        cases = list(Case.objects.filter(user=user).filter(q).select_related("court")[:3])
    return [{"case_id": str(c.id), "cnr_number": c.cnr_number, "case_number": c.case_number, "title": c.case_title,
             "court": c.court.name if c.court else None, "status": c.status, "next_hearing_date":
             c.next_hearing_date.isoformat() if c.next_hearing_date else None,
             "source_type": "CASE_RECORD", "data_origin": c.data_origin, "is_demo_data": c.is_demo_data,
             "last_updated": c.updated_at.isoformat()} for c in cases]


def build_next_steps(draft, intake, evidence: EvidenceSet, lang: str, safety: LegalSafetyService) -> List[dict]:
    """Prefer steps from the grounded answer; otherwise curated hedged playbook options. A step is only
    `source_backed` when it cites a retrieved source."""
    steps: List[dict] = []
    for s in draft.next_steps:
        steps.append({"title": s.title, "detail": s.detail, "kind": "POSSIBLE_OPTION",
                      "source_ids": s.source_ids, "source_backed": bool(s.source_ids)})
    if not steps:
        have_keys: Dict[str, str] = {e.key: lab for lab, e in evidence.items.items() if e.key}
        for k in playbooks.select_steps(intake.legal_topic, intake.issue_flags, bool(intake.existing_case)):
            b = playbooks.build(k, lang)
            ids = [have_keys[x] for x in b["keys"] if x in have_keys]
            steps.append({"title": b["title"], "detail": b["description"], "kind": b["kind"],
                          "source_ids": ids, "source_backed": bool(ids)})
    cleaned = []
    for st, (txt, _) in zip(steps, safety.inspect_items([s["detail"] for s in steps], lang)):
        if txt:
            st["detail"] = txt
            cleaned.append(st)
    return cleaned[:6]


class ChatOrchestrator:
    def __init__(self, provider=None, embedder=None):
        self.provider = provider or get_ai_provider()
        self.intake_svc = LegalIntakeService(self.provider)
        self.research_svc = LegalResearchService(self.provider, embedder)
        self.answer_svc = GroundedAnswerService(self.provider)
        self.citations = CitationVerificationService()
        self.safety = LegalSafetyService()
        self.followups = FollowUpService()

    # ------------------------------------------------------------------ conversation helpers
    @staticmethod
    def _conversation(user, conversation_id, case, lang) -> Optional[Conversation]:
        if user is None or not getattr(user, "is_authenticated", False):
            return None  # guests are stateless: nothing is stored that another guest could fetch
        if conversation_id:
            conv = Conversation.objects.filter(pk=conversation_id, user=user).first()
            if conv:
                return conv
        return Conversation.objects.create(user=user, case=case, language=lang)

    def chat(self, message: str, user=None, language: Optional[str] = None, conversation_id=None, case=None) -> dict:
        message = (message or "").strip()[: settings.AI_MAX_INPUT_CHARS]
        call = AICall(user, AIRequestType.CHAT, self.provider, message)
        conv = self._conversation(user, conversation_id, case, language or "en")
        ctx = dict(conv.context) if conv else {}

        intake = self.intake_svc.analyze(message, ctx, case)
        lang = response_language(language, intake.language, getattr(user, "preferred_language", None))
        if conv:
            ConversationMessage.objects.create(conversation=conv, role=MessageRole.USER, content=message)

        questions = self.followups.questions(intake, lang, has_case_record=case is not None)
        too_vague = intake.legal_topic == "OTHER" and not intake.search_keywords and not intake.key_issues

        hits, evidence = [], EvidenceSet()
        outcome = None
        if not too_vague:
            filters = SearchFilters(state=intake.state, district=None,
                                    topic=intake.legal_topic if intake.legal_topic != "OTHER" else None)
            try:
                outcome = self.research_svc.research(intake, message, filters=filters, top_k=settings.RETRIEVAL_TOP_K)
                hits = outcome.hits
                evidence = evidence_from_hits(hits, lang)
            except Exception as exc:  # noqa: BLE001 - retrieval failure degrades to "not found", never a crash
                logger.error("research_failed", extra={"service": "chat", "error_type": type(exc).__name__})

        if too_vague:
            from ai.schemas import GroundedAnswer  # noqa: F401
            answer_text, claims, unknowns, degraded = CLARIFY[lang], [], ["The problem has not been described yet"], False
            report_status, sources, steps_src = "pending_more_info", [], []
            draft = None
            safe_text, safe_flags = answer_text, []
            next_steps: List[dict] = []
        else:
            draft = self.answer_svc.answer(message, lang, self._context_str(intake), evidence)
            report = self.citations.verify(draft.answer, evidence, lang=lang,
                                           claim_labels=[s for c in draft.claims for s in c.source_ids])
            safe = self.safety.inspect(report.answer, lang=lang, source_text=evidence.text_blob() or None)
            safe_text, safe_flags = safe.text, safe.flags
            claims = [{"text": t, "kind": c.kind, "source_ids": c.source_ids}
                      for c, (t, _) in zip(draft.claims, self.safety.inspect_items([c.text for c in draft.claims], lang,
                                                                                   evidence.text_blob()))
                      if t]
            unknowns, degraded = draft.unknowns, draft.degraded
            report_status, sources = report.status, report.sources
            next_steps = build_next_steps(draft, intake, evidence, lang, self.safety)

        warnings = [f.as_dict() for f in safe_flags if f.code != "DISCLAIMER_ADDED"]
        if not too_vague:
            if draft is not None and not evidence:
                warnings.append({"code": "NO_VERIFIED_SOURCES", "severity": "INFO",
                                 "detail": "No matching verified source was found; nothing here should be treated as a legal source."})
            if any(s.get("is_demo_data") for s in sources):
                warnings.append({"code": "DEMO_DATA", "severity": "WARNING", "detail": DEMO_NOTICE[lang]})
            warnings += [{"code": "CITATION_ISSUE", "severity": "WARNING", "detail": w} for w in getattr(report, "warnings", [])]

        sources_out = [s for s in sources if s.get("cited")] or sources
        judgment_refs = [s for s in sources_out if s.get("judgment_id")]
        refs = case_references(user, intake, case)
        result = {
            "answer": safe_text, "language": lang, "conversation_id": str(conv.id) if conv else None,
            "detected_intent": intake.legal_topic, "detected_language": intake.language,
            "entities": entities_of(intake), "follow_up_questions": questions,
            "sources": sources_out, "judgment_references": judgment_refs, "case_references": refs,
            "claims": claims, "next_steps": next_steps, "unknowns": unknowns, "warnings": warnings,
            "verification_status": report_status, "disclaimer": DISCLAIMER[lang],
            "similarity_note": None, "is_degraded": degraded, "provider": self.provider.name,
            "search": {"queries": outcome.queries if outcome else [], "filters": outcome.filters.as_dict() if outcome else {},
                       "retrieved_at_note": "Results come from stored (cached) sources, not live court systems."},
        }

        call.success(safe_text, lang, report_status, {k: result[k] for k in ("detected_intent", "verification_status",
                                                                              "follow_up_questions", "sources")},
                     [f.code for f in safe_flags])
        if conv:
            ConversationMessage.objects.create(conversation=conv, role=MessageRole.ASSISTANT, content=safe_text)
            conv.context = {**conv.context, **intake_to_context(intake)}
            if not conv.title:
                conv.title = message[:80]
            conv.save(update_fields=["context", "title", "updated_at"])
        if outcome and user is not None and getattr(user, "is_authenticated", False):
            try:
                LegalResearchService.record(user, SearchKind.RESEARCH, message, outcome, lang)
            except Exception:  # noqa: BLE001
                pass
        return result

    @staticmethod
    def _context_str(intake) -> str:
        known = {k: v for k, v in entities_of(intake).items() if v not in (None, [], "")}
        unknown = [k for k in ("state", "district", "case_number") if not getattr(intake, k) and not (k == "case_number" and intake.cnr)]
        return f"topic: {intake.legal_topic}; known: {known}; unknown: {unknown}"
