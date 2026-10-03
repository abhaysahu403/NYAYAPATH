"""Case CRUD + search endpoints."""
import logging

from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from audit import services as audit_svc
from audit.models import AuditEventType
from core.exceptions import NotFoundError, ValidationError, PermissionDeniedError
from core.pagination import StandardPagination
from core.renderers import NyayaRenderer
from .models import Case, CaseEvent, CaseParty, Hearing
from .serializers import (
    CaseSerializer, CaseCreateSerializer, CaseEventSerializer,
    HearingSerializer, CaseSearchSerializer, CasePartySerializer,
)

logger = logging.getLogger("nyayapath.cases")


def _get_case(pk, user):
    try:
        case = Case.objects.select_related("court", "source").prefetch_related("parties", "events", "hearings").get(pk=pk)
    except Case.DoesNotExist:
        raise NotFoundError("Case not found.")
    if case.user_id != user.id and not user.is_admin:
        raise PermissionDeniedError()
    return case


class CaseListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def get(self, request):
        qs = Case.objects.filter(user=request.user).select_related("court").order_by("-created_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(CaseSerializer(page, many=True).data)

    def post(self, request):
        ser = CaseCreateSerializer(data=request.data, context={"request": request})
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        case = ser.save()
        audit_svc.record(AuditEventType.CASE_CREATED, request=request, resource_type="Case",
                         resource_id=case.id, description=f"Case created: {case}")
        return Response(CaseSerializer(case, context={"request": request}).data, status=status.HTTP_201_CREATED)


class CaseDetailView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def get(self, request, pk):
        case = _get_case(pk, request.user)
        return Response(CaseSerializer(case).data)

    def patch(self, request, pk):
        case = _get_case(pk, request.user)
        ser = CaseCreateSerializer(case, data=request.data, partial=True, context={"request": request})
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        ser.save()
        return Response(CaseSerializer(case).data)

    def delete(self, request, pk):
        case = _get_case(pk, request.user)
        audit_svc.record(AuditEventType.CASE_DELETED, request=request, resource_type="Case",
                         resource_id=pk, description=f"Case deleted")
        case.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CaseSearchView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def post(self, request):
        ser = CaseSearchSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        d = ser.validated_data
        qs = Case.objects.filter(user=request.user).select_related("court")
        if d.get("cnr"):
            qs = qs.filter(cnr_number__icontains=d["cnr"])
        if d.get("case_number"):
            qs = qs.filter(case_number__icontains=d["case_number"])
        if d.get("case_type"):
            qs = qs.filter(case_type=d["case_type"])
        if d.get("status"):
            qs = qs.filter(status=d["status"])
        if d.get("state"):
            qs = qs.filter(state__icontains=d["state"])
        if d.get("district"):
            qs = qs.filter(district__icontains=d["district"])
        if d.get("year"):
            qs = qs.filter(filing_year=d["year"])
        if d.get("q"):
            qs = qs.filter(Q(case_title__icontains=d["q"]) | Q(description__icontains=d["q"]))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs.order_by("-created_at"), request)
        return paginator.get_paginated_response(CaseSerializer(page, many=True).data)


class CaseTimelineView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def get(self, request, pk):
        case = _get_case(pk, request.user)
        events = case.events.order_by("event_date")
        return Response({"events": CaseEventSerializer(events, many=True).data})

    def post(self, request, pk):
        case = _get_case(pk, request.user)
        ser = CaseEventSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        event = ser.save(case=case, data_origin="USER_PROVIDED")
        return Response(CaseEventSerializer(event).data, status=status.HTTP_201_CREATED)


class CaseHearingView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def get(self, request, pk):
        case = _get_case(pk, request.user)
        return Response({"hearings": HearingSerializer(case.hearings.order_by("-hearing_date"), many=True).data})

    def post(self, request, pk):
        case = _get_case(pk, request.user)
        ser = HearingSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        hearing = ser.save(case=case)
        return Response(HearingSerializer(hearing).data, status=status.HTTP_201_CREATED)


class CasePartyView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [NyayaRenderer]

    def get(self, request, pk):
        case = _get_case(pk, request.user)
        return Response({"parties": CasePartySerializer(case.parties.all(), many=True).data})

    def post(self, request, pk):
        case = _get_case(pk, request.user)
        ser = CasePartySerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        party = ser.save(case=case)
        return Response(CasePartySerializer(party).data, status=status.HTTP_201_CREATED)
