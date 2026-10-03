from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from core.pagination import StandardPagination
from core.renderers import NyayaRenderer
from rest_framework.response import Response
from core.exceptions import NotFoundError
from .models import Source
from .serializers import SourceSerializer


class SourceListView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [NyayaRenderer]

    def get(self, request):
        qs = Source.objects.all().order_by("-retrieved_at")
        source_type = request.query_params.get("source_type")
        verification_status = request.query_params.get("verification_status")
        if source_type:
            qs = qs.filter(source_type=source_type)
        if verification_status:
            qs = qs.filter(verification_status=verification_status)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(SourceSerializer(page, many=True).data)


class SourceDetailView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [NyayaRenderer]

    def get(self, request, pk):
        try:
            source = Source.objects.get(pk=pk)
        except Source.DoesNotExist:
            raise NotFoundError("Source not found.")
        return Response(SourceSerializer(source).data)
