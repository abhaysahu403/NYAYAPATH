import logging
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from audit import services as audit_svc
from audit.models import AuditEventType
from core.exceptions import NotFoundError, ValidationError, PermissionDeniedError
from core.pagination import StandardPagination
from core.renderers import NyayaRenderer
from .models import ActionPlan, ActionStep, ActionStepStatus
from .serializers import ActionPlanSerializer, ActionPlanGenerateSerializer

logger = logging.getLogger("nyayapath.action_plans")


def _get_plan(pk, user):
    try:
        plan = ActionPlan.objects.prefetch_related("steps").get(pk=pk)
    except ActionPlan.DoesNotExist:
        raise NotFoundError("Action plan not found.")
    if plan.user_id != user.id and not user.is_admin:
        raise PermissionDeniedError()
    return plan


class ActionPlanListView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def get(self, request):
        qs = ActionPlan.objects.filter(user=request.user).prefetch_related("steps").order_by("-created_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(ActionPlanSerializer(page, many=True).data)


class ActionPlanGenerateView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def post(self, request):
        ser = ActionPlanGenerateSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        d = ser.validated_data
        case = None
        if d.get("case_id"):
            from cases.models import Case
            try:
                case = Case.objects.get(pk=d["case_id"], user=request.user)
            except Case.DoesNotExist:
                raise ValidationError("Case not found.")

        from ai.providers.factory import get_ai_provider
        from ai.schemas import PlanResult
        from ai.services.intake import LegalIntakeService
        from ai.services.language import response_language
        from ai.services.retrieval_context import evidence_from_hits
        from ai.services.safety import DISCLAIMER, LegalSafetyService
        from ai.services.tracking import AICall
        from ai.models import AIRequestType
        from legal_research.services.research import LegalResearchService
        from legal_research.services.search import SearchFilters

        provider = get_ai_provider()
        intake = LegalIntakeService(provider).analyze(d["message"], {}, case)
        lang = response_language(d.get("language"), intake.language, request.user.preferred_language)
        call = AICall(request.user, AIRequestType.ACTION_PLAN, provider, d["message"])

        filters = SearchFilters(state=intake.state, topic=intake.legal_topic if intake.legal_topic != "OTHER" else None)
        try:
            hits = LegalResearchService(provider).research(intake, d["message"], filters=filters, top_k=6).hits
        except Exception:  # noqa: BLE001
            hits = []
        evidence = evidence_from_hits(hits, lang)
        valid = set(evidence.items)

        known = {k: v for k, v in intake.model_dump().items() if v not in (None, [], "")}
        facts = f"USER-PROVIDED / EXTRACTED FACTS: {known}"
        unknowns = ", ".join(k for k in ("state", "district", "case_number") if not getattr(intake, k)) or "none identified"
        try:
            raw = provider.generate_action_plan(lang, facts, unknowns, evidence.passages(), topic=intake.legal_topic,
                                                flags=intake.issue_flags)
            plan_schema = PlanResult.model_validate(raw.data)
            degraded = False
        except Exception as exc:  # noqa: BLE001
            logger.warning("action_plan_generation_failed: %s", type(exc).__name__)
            call.failure(type(exc).__name__)
            from ai.services import playbooks
            from ai.schemas import PlanStep
            keys = playbooks.select_steps(intake.legal_topic, intake.issue_flags, bool(intake.existing_case))
            steps = []
            for k in keys:
                b = playbooks.build(k, lang)
                steps.append(PlanStep(title=b["title"], description=b["description"], why_relevant=b["why_relevant"],
                                      required_documents=b["required_documents"], kind=b["kind"], difficulty=b["difficulty"]))
            plan_schema = PlanResult(title="Possible next steps" if lang == "en" else "संभावित अगले कदम",
                                     situation_assessment="Based on the available information, these are possible options to verify with a legal professional."
                                     if lang == "en" else "उपलब्ध जानकारी के आधार पर ये संभावित विकल्प हैं; इन्हें वकील से सत्यापित करें।",
                                     steps=steps or [PlanStep(title="Consult a legal professional", description="Discuss your situation with a qualified lawyer or legal aid authority.")])
            degraded = True

        safety = LegalSafetyService()
        src_text = evidence.text_blob() or None
        assessment = safety.inspect(plan_schema.situation_assessment, lang=lang, add_disclaimer=False)
        warnings = [t for t, _ in safety.inspect_items(plan_schema.warnings, lang) if t]
        if any(e.is_demo for e in evidence.items.values()):
            warnings.append("Some sources are DEMO data, not real legal authority." if lang == "en"
                            else "कुछ स्रोत DEMO डेटा हैं, वास्तविक कानूनी प्राधिकार नहीं।")
        supporting = [e.as_source_dict(cited=True) for e in evidence.items.values()]

        plan = ActionPlan.objects.create(
            user=request.user, case=case, title=plan_schema.title[:500], situation_assessment=assessment.text,
            delay_cause_analysis=(safety.inspect(plan_schema.delay_cause_analysis, lang, src_text, add_disclaimer=False).text
                                  if plan_schema.delay_cause_analysis else None),
            immediate_priority=plan_schema.immediate_priority, warnings=warnings, supporting_sources=supporting,
            original_query=d["message"][:2000], intake_analysis=intake.model_dump(), language=lang,
            evidence={"fact_basis": "user_provided_or_extracted", "sources_retrieved": len(supporting), "degraded": degraded},
            disclaimer=DISCLAIMER[lang])
        n = 0
        for step in plan_schema.steps:
            text, _ = safety.inspect_items([step.description], lang, src_text)[0]
            if not text:
                continue
            n += 1
            ids = [i for i in step.source_ids if i in valid]
            ActionStep.objects.create(
                action_plan=plan, step_number=n, title=step.title[:300], description=text, why_relevant=step.why_relevant,
                documents_needed=step.required_documents, legal_basis=step.legal_basis if ids else None,
                estimated_timeline=None, difficulty=step.difficulty, source_references=ids, kind=step.kind,
                source_backed=bool(ids))
        call.success(plan.title, lang, "plan", {"plan_id": str(plan.id)}, [])

        audit_svc.record(AuditEventType.ACTION_PLAN_GENERATED, request=request,
                         resource_type="ActionPlan", resource_id=plan.id)
        plan.refresh_from_db()
        return Response(ActionPlanSerializer(plan).data, status=status.HTTP_201_CREATED)


class ActionPlanDetailView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def get(self, request, pk):
        return Response(ActionPlanSerializer(_get_plan(pk, request.user)).data)

    def delete(self, request, pk):
        plan = _get_plan(pk, request.user)
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActionStepCompleteView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def post(self, request, pk, step_id):
        plan = _get_plan(pk, request.user)
        try:
            step = plan.steps.get(pk=step_id)
        except ActionStep.DoesNotExist:
            raise NotFoundError("Step not found.")
        step.status = ActionStepStatus.COMPLETED
        step.completed_at = timezone.now()
        step.save(update_fields=["status", "completed_at"])
        from .serializers import ActionStepSerializer
        return Response(ActionStepSerializer(step).data)
