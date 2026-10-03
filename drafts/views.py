import logging
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit import services as audit_svc
from audit.models import AuditEventType
from core.exceptions import NotFoundError, ValidationError, PermissionDeniedError
from core.pagination import StandardPagination
from core.renderers import NyayaRenderer
from .models import GeneratedDraft
from .serializers import DraftSerializer, CaseSummaryRequestSerializer, LawyerBriefRequestSerializer, RTIRequestSerializer
from .services import DraftGenerationService

logger = logging.getLogger("nyayapath.drafts")


def _get_draft(pk, user):
    try:
        draft = GeneratedDraft.objects.get(pk=pk)
    except GeneratedDraft.DoesNotExist:
        raise NotFoundError("Draft not found.")
    if draft.user_id != user.id and not user.is_admin:
        raise PermissionDeniedError()
    return draft


def _resolve_case(case_id, user):
    if not case_id:
        return None
    from cases.models import Case
    try:
        return Case.objects.get(pk=case_id, user=user)
    except Case.DoesNotExist:
        raise ValidationError("Case not found.")


def _do_research(intake):
    from legal_research.services.research import LegalResearchService
    from legal_research.services.search import SearchFilters
    try:
        svc = LegalResearchService()
        filters = SearchFilters(state=intake.state,
                                topic=intake.legal_topic if intake.legal_topic != "OTHER" else None)
        outcome = svc.research(intake, " ".join(intake.search_keywords), filters=filters, top_k=5)
        return outcome.hits
    except Exception as exc:
        logger.warning("draft_research_failed: %s", exc)
        return []


class DraftListView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def get(self, request):
        qs = GeneratedDraft.objects.filter(user=request.user).order_by("-created_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(DraftSerializer(page, many=True).data)


class DraftDetailView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def get(self, request, pk):
        return Response(DraftSerializer(_get_draft(pk, request.user)).data)

    def delete(self, request, pk):
        _get_draft(pk, request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CaseSummaryView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def post(self, request):
        ser = CaseSummaryRequestSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        d = ser.validated_data
        case = _resolve_case(d.get("case_id"), request.user)
        from ai.services.intake import LegalIntakeService
        intake = LegalIntakeService().analyze(d["message"], {}, case)
        hits = _do_research(intake)
        lang = d["language"]
        draft = DraftGenerationService().generate_case_summary(request.user, intake, case, hits, lang)
        audit_svc.record(AuditEventType.DRAFT_GENERATED, request=request,
                         resource_type="GeneratedDraft", resource_id=draft.id,
                         description="Case summary generated")
        return Response(DraftSerializer(draft).data, status=status.HTTP_201_CREATED)


class LawyerBriefView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def post(self, request):
        ser = LawyerBriefRequestSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        d = ser.validated_data
        case = _resolve_case(d.get("case_id"), request.user)
        from ai.services.intake import LegalIntakeService
        intake = LegalIntakeService().analyze(d["message"], {}, case)
        hits = _do_research(intake)
        draft = DraftGenerationService().generate_lawyer_brief(
            request.user, intake, case, hits, d["language"],
            d.get("lawyer_name", ""), d.get("court_name", ""),
        )
        audit_svc.record(AuditEventType.DRAFT_GENERATED, request=request,
                         resource_type="GeneratedDraft", resource_id=draft.id,
                         description="Lawyer brief generated")
        return Response(DraftSerializer(draft).data, status=status.HTTP_201_CREATED)


class RTIDraftView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def post(self, request):
        ser = RTIRequestSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        d = ser.validated_data
        case = _resolve_case(d.get("case_id"), request.user)
        from ai.services.intake import LegalIntakeService
        intake = LegalIntakeService().analyze(d["message"], {}, case)
        hits = _do_research(intake)
        draft = DraftGenerationService().generate_rti(
            request.user, intake, case, hits, d["language"],
            d.get("applicant_name", ""), d.get("public_authority", ""),
            d.get("information_sought", ""),
        )
        audit_svc.record(AuditEventType.DRAFT_GENERATED, request=request,
                         resource_type="GeneratedDraft", resource_id=draft.id,
                         description="RTI draft generated")
        return Response(DraftSerializer(draft).data, status=status.HTTP_201_CREATED)
