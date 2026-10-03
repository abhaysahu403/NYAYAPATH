"""AI API: chat, conversations, judgment explanation, similar-case search, feedback."""
import logging

from django.conf import settings
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit import services as audit_svc
from audit.models import AuditEventType
from core.exceptions import NotFoundError, ValidationError
from core.pagination import StandardPagination
from core.throttles import AIChatThrottle, AIGuestThrottle, AIHeavyThrottle
from ai.models import AIRequestType, AIResponse, Conversation
from ai.providers.factory import get_ai_provider
from ai.schemas import JudgmentExplanation
from ai.services.chat import ChatOrchestrator
from ai.services.intake import LegalIntakeService
from ai.services.language import response_language
from ai.services.safety import LegalSafetyService
from ai.services.tracking import AICall
from judgments.models import Judgment
from legal_research.models import KnowledgeChunk, SearchKind
from legal_research.services.research import SIMILARITY_NOTE, LegalResearchService, hit_to_dict
from legal_research.services.search import SearchFilters

logger = logging.getLogger("nyayapath.ai.views")


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=3, max_length=settings.AI_MAX_INPUT_CHARS, trim_whitespace=True)
    language = serializers.ChoiceField(choices=["hi", "en"], required=False, allow_null=True)
    case_id = serializers.UUIDField(required=False, allow_null=True)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)


class ChatView(APIView):
    """POST /api/v1/ai/chat/ — guests may use it (stricter rate limit, nothing stored)."""
    permission_classes = [AllowAny]
    throttle_classes = [AIChatThrottle, AIGuestThrottle]

    def post(self, request):
        ser = ChatRequestSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        d = ser.validated_data
        case = None
        if d.get("case_id"):
            if not request.user.is_authenticated:
                raise ValidationError("Please log in to use a saved case.", code="LOGIN_REQUIRED")
            from cases.models import Case
            case = Case.objects.filter(pk=d["case_id"], user=request.user).select_related("court").first()
            if case is None:
                raise NotFoundError("Case not found.", code="CASE_NOT_FOUND")
        result = ChatOrchestrator().chat(d["message"], user=request.user, language=d.get("language"),
                                         conversation_id=d.get("conversation_id"), case=case)
        audit_svc.record(AuditEventType.AI_CHAT, request=request, description="AI chat request",
                         metadata={"intent": result["detected_intent"], "status": result["verification_status"]})
        return Response(result)


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Conversation.objects.filter(user=request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response([
            {"id": str(c.id), "title": c.title or "Conversation", "language": c.language,
             "created_at": c.created_at, "updated_at": c.updated_at} for c in page])


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _get(pk, user):
        conv = Conversation.objects.filter(pk=pk, user=user).first()
        if conv is None:
            raise NotFoundError("Conversation not found.", code="CONVERSATION_NOT_FOUND")
        return conv

    def get(self, request, pk):
        conv = self._get(pk, request.user)
        return Response({"id": str(conv.id), "title": conv.title, "language": conv.language, "context": conv.context,
                         "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at}
                                      for m in conv.messages.all()]})

    def delete(self, request, pk):
        self._get(pk, request.user).delete()
        audit_svc.record(AuditEventType.CONVERSATION_DELETED, request=request, resource_type="Conversation", resource_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FeedbackSerializer(serializers.Serializer):
    rating = serializers.ChoiceField(choices=[-1, 1])
    comment = serializers.CharField(required=False, allow_blank=True, max_length=500)


class JudgmentExplainView(APIView):
    """POST /api/v1/ai/judgments/<id>/explain/ — plain-language explanation built only from the stored judgment."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIHeavyThrottle]

    def post(self, request, pk):
        j = Judgment.objects.select_related("court", "source").filter(pk=pk).first()
        if j is None:
            raise NotFoundError("Judgment not found.", code="JUDGMENT_NOT_FOUND")
        question = (request.data.get("question") or "").strip()[:500]
        lang = response_language(request.data.get("language"), None, request.user.preferred_language)

        chunks = list(KnowledgeChunk.objects.filter(judgment=j).order_by("chunk_index")[:8])
        locator = lambda c: c.section_title or (f"p. {c.page_number}" if c.page_number else f"part {c.chunk_index + 1}")  # noqa: E731
        if chunks:
            passages = [{"label": f"S{i}", "text": c.text, "title": j.title, "citation": j.citation, "locator": locator(c)}
                        for i, c in enumerate(chunks, 1)]
        elif j.summary or j.full_text:
            passages = [{"label": "S1", "text": (j.full_text or j.summary)[:settings.DOCUMENT_ANALYSIS_MAX_CHARS],
                         "title": j.title, "citation": j.citation, "locator": None}]
        else:
            raise ValidationError("No text is stored for this judgment, so it cannot be explained.", code="NO_TEXT")

        provider = get_ai_provider()
        call = AICall(request.user, AIRequestType.JUDGMENT_EXPLAIN, provider, f"{j.id}:{question}")
        try:
            exp = JudgmentExplanation.model_validate(provider.summarize_judgment(question, lang, passages).data)
            degraded = False
        except Exception as exc:  # noqa: BLE001
            call.failure(type(exc).__name__)
            exp = JudgmentExplanation(plain_summary=(j.summary or passages[0]["text"])[:600])
            degraded = True
        safety = LegalSafetyService()
        src_text = " ".join(p["text"] for p in passages)
        summary = safety.inspect(exp.plain_summary, lang=lang, source_text=src_text)
        cleaned = {f: (safety.inspect(getattr(exp, f), lang, src_text, add_disclaimer=False).text if getattr(exp, f) else None)
                   for f in ("legal_issue", "court_reasoning", "outcome", "relevance_to_question")}
        facts = [t for t, _ in safety.inspect_items(exp.key_facts, lang, src_text) if t]
        if not degraded:
            call.success(summary.text, lang, j.verification_status.lower(), {"judgment_id": str(j.id)}, summary.flag_codes)
        audit_svc.record(AuditEventType.JUDGMENT_EXPLAINED, request=request, resource_type="Judgment", resource_id=j.id)
        warnings = [f.as_dict() for f in summary.flags if f.code != "DISCLAIMER_ADDED"]
        if j.is_demo_data:
            warnings.append({"code": "DEMO_DATA", "severity": "WARNING",
                             "detail": "This judgment record is DEMO data and is not a real judgment."})
        return Response({
            "judgment": {"id": str(j.id), "title": j.title, "citation": j.citation, "court": j.court.name if j.court else None,
                         "date": j.judgment_date, "source_url": j.source_url, "verification_status": j.verification_status,
                         "is_demo_data": j.is_demo_data},
            "explanation": {"plain_summary": summary.text, "key_facts": facts, **cleaned},
            "grounding": [{"label": p["label"], "locator": p["locator"]} for p in passages],
            "language": lang, "is_degraded": degraded, "warnings": warnings,
            "note": "Explanation is generated from the stored judgment text only; read the original judgment before relying on it.",
        })


class SimilarCasesView(APIView):
    """POST /api/v1/ai/similar-cases/ — semantically similar judgments in the indexed corpus."""
    permission_classes = [AllowAny]
    throttle_classes = [AIHeavyThrottle, AIGuestThrottle]

    def post(self, request):
        message = (request.data.get("message") or "").strip()
        if len(message) < 5:
            raise ValidationError("Please describe your situation (at least a few words).", code="MESSAGE_REQUIRED")
        message = message[: settings.AI_MAX_INPUT_CHARS]
        try:
            top_k = max(1, min(int(request.data.get("top_k", 10)), settings.RETRIEVAL_MAX_TOP_K))
        except (TypeError, ValueError):
            raise ValidationError("top_k must be a number.")
        provider = get_ai_provider()
        intake = LegalIntakeService(provider).analyze(message, {})
        lang = response_language(request.data.get("language"), intake.language, getattr(request.user, "preferred_language", None))
        filters = SearchFilters(state=request.data.get("state") or intake.state, court=request.data.get("court") or None,
                                topic=request.data.get("topic") or (intake.legal_topic if intake.legal_topic != "OTHER" else None),
                                judgments_only=True)
        svc = LegalResearchService(provider)
        outcome = svc.research(intake, message, filters=filters, top_k=top_k, judgments_only=True)
        if request.user.is_authenticated:
            LegalResearchService.record(request.user, SearchKind.SIMILAR_CASE, message, outcome, lang)
        return Response({
            "results": [hit_to_dict(h, outcome.filters, lang) for h in outcome.hits], "count": len(outcome.hits),
            "similarity_note": SIMILARITY_NOTE[lang], "detected_topic": intake.legal_topic, "detected_state": intake.state,
            "filters": outcome.filters.as_dict(), "queries": outcome.queries,
            "data_freshness": "Results come from stored (cached) sources, not live court systems.",
        })


class ResponseFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        ser = FeedbackSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        resp = AIResponse.objects.filter(pk=pk, request__user=request.user).first()
        if resp is None:
            raise NotFoundError("Response not found.")
        resp.feedback_rating = ser.validated_data["rating"]
        resp.feedback_comment = ser.validated_data.get("comment", "")
        resp.save(update_fields=["feedback_rating", "feedback_comment"])
        return Response({"saved": True})
