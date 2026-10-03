from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from core.pagination import StandardPagination
from core.renderers import NyayaRenderer
from .models import Court
from .serializers import CourtSerializer


class CourtListView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [NyayaRenderer]

    def get(self, request):
        qs = Court.objects.filter(active=True)
        state = request.query_params.get("state")
        court_type = request.query_params.get("court_type")
        q = request.query_params.get("q")
        if state:
            qs = qs.filter(state__icontains=state)
        if court_type:
            qs = qs.filter(court_type=court_type.upper())
        if q:
            qs = qs.filter(name__icontains=q)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs.order_by("name"), request)
        return paginator.get_paginated_response(CourtSerializer(page, many=True).data)


class CourtDetailView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [NyayaRenderer]

    def get(self, request, pk):
        from core.exceptions import NotFoundError
        try:
            court = Court.objects.get(pk=pk, active=True)
        except Court.DoesNotExist:
            raise NotFoundError("Court not found.")
        return Response(CourtSerializer(court).data)
