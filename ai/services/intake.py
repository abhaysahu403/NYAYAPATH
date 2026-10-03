"""LegalIntakeService: language, intent, entities, missing information -> validated IntakeResult.

The LLM output is UNTRUSTED. It is schema-validated, and identifiers/places are cross-checked against the
user's own text with deterministic extractors so the model can never invent a CNR, state or district.
"""
import logging
from typing import Optional

from django.conf import settings
from pydantic import ValidationError

from ai.providers.factory import get_ai_provider
from ai.schemas import TOPIC_CODES, IntakeResult
from ai.services import glossary, heuristics
from core.exceptions import NyayaError

logger = logging.getLogger("nyayapath.ai.intake")

CONTEXT_FIELDS = ("state", "district", "court", "cnr", "case_number", "existing_case", "case_age_years", "property_type")


def _state_in_text(state: str, low: str) -> bool:
    aliases = glossary.STATES.get(state, []) + [state.lower()]
    return any(a.strip() and a.strip() in low for a in aliases)


def intake_to_context(intake: IntakeResult) -> dict:
    ctx = {k: getattr(intake, k) for k in CONTEXT_FIELDS if getattr(intake, k) is not None}
    if intake.legal_topic != "OTHER":
        ctx["legal_topic"] = intake.legal_topic
    if intake.documents:
        ctx["documents"] = intake.documents
    if intake.issue_flags:
        ctx["issue_flags"] = intake.issue_flags
    return ctx


class LegalIntakeService:
    def __init__(self, provider=None):
        self._provider = provider

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_ai_provider()
        return self._provider

    def analyze(self, text: str, context: Optional[dict] = None, case=None) -> IntakeResult:
        text = (text or "").strip()[: settings.AI_MAX_INPUT_CHARS]
        det = heuristics.analyse(text)
        try:
            result = IntakeResult.model_validate(self.provider.analyze_intake(text, sorted(TOPIC_CODES)).data)
        except (NyayaError, ValidationError, TypeError, AttributeError):
            logger.warning("intake_fallback_to_heuristics", extra={"service": "intake"})
            result = IntakeResult.model_validate(det)
        return self._reconcile(result, det, text, context or {}, case)

    # ------------------------------------------------------------------ helpers
    def _reconcile(self, r: IntakeResult, det: dict, text: str, ctx: dict, case) -> IntakeResult:
        low = f" {text.lower()} "
        r.language = det["language"]                      # deterministic, never LLM
        r.cnr = det["cnr"]                                  # only a CNR literally present in the text
        cn = r.case_number if (r.case_number and r.case_number.replace(" ", "") in text.replace(" ", "")) else None
        r.case_number = det["case_number"] or cn
        # state / district must be grounded in the user's text (or their own earlier context)
        if r.state and not _state_in_text(r.state, low):
            r.state = None
        r.state = det["state"] or r.state
        if r.district and r.district.lower() not in low:
            r.district = None
        r.district = det["district"] or r.district
        if not r.state and r.district:
            r.state = heuristics.extract_district(r.district)[1]
        if r.legal_topic == "OTHER" and det["legal_topic"] != "OTHER":
            r.legal_topic = det["legal_topic"]
        r.issue_flags = sorted(set(r.issue_flags) | set(det["issue_flags"]))[:6]
        r.search_keywords = list(dict.fromkeys(list(r.search_keywords) + det["search_keywords"]))[:12]
        r.documents = list(dict.fromkeys(list(r.documents) + det["documents"]))[:10]
        if det["case_age_years"] is not None:
            r.case_age_years = det["case_age_years"]
        if det["existing_case"] is not None:
            r.existing_case = det["existing_case"]
        if det["property_size"] and not r.property_size:
            r.property_size = det["property_size"]
        # fill gaps from earlier conversation context, then from an explicitly selected case record
        for k in CONTEXT_FIELDS:
            if getattr(r, k) is None and ctx.get(k) is not None:
                setattr(r, k, ctx[k])
        if r.legal_topic == "OTHER" and ctx.get("legal_topic") in TOPIC_CODES:
            r.legal_topic = ctx["legal_topic"]
        if ctx.get("documents"):
            r.documents = list(dict.fromkeys(list(r.documents) + list(ctx["documents"])))[:10]
        if ctx.get("issue_flags"):
            r.issue_flags = sorted(set(r.issue_flags) | set(ctx["issue_flags"]))[:6]
        if case is not None:
            r.existing_case = True
            r.state = r.state or case.state
            r.district = r.district or case.district
            r.cnr = r.cnr or case.cnr_number
            r.case_number = r.case_number or case.case_number
            if case.court_id and not r.court:
                r.court = case.court.name
        return r
