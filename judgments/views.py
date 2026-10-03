"""Judgment search (hybrid, paginated, ranked), browse and detail."""
import logging

from django.db.models import Q
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.services import heuristics
from ai.services.language import detect_language, response_language
from core.exceptions import NotFoundError, ValidationError
from core.pagination import StandardPagination, paginate_list
from core.throttles import JudgmentSearchThrottle
from legal_research.models import SearchKind
from legal_research.services.research import SIMILARITY_NOTE, LegalResearchService, ResearchOutcome, hit_to_dict
from legal_research.services.search import HybridSearchService, SearchFilters
from .models import Judgment
from .serializers import JudgmentListSerializer, JudgmentSearchSerializer, JudgmentSerializer

logger = logging.getLogger("nyayapath.judgments")


class JudgmentSearchView(APIView):
    """POST /api/v1/judgments/search/ — semantic + keyword + metadata filters, results paginated (?page=&page_size=)."""
    permission_classes = [AllowAny]
    throttle_classes = [JudgmentSearchThrottle]

    def post(self, request):
        ser = JudgmentSearchSerializer(data=request.data)
        if not ser.is_valid():
            raise ValidationError(detail=ser.errors)
        d = ser.validated_data
        filters = SearchFilters(state=d.get("state") or None, court=d.get("court") or None, district=d.get("district") or None,
                                topic=d.get("topic") or None, date_from=d.get("date_from"), date_to=d.get("date_to"),
                                language=d.get("language") or None, source_type=d.get("source_type") or None,
                                judgments_only=d.get("judgments_only", True))
        keywords = heuristics.expand_keywords(d["query"])
        queries = [d["query"]] + ([" ".join(keywords[:8])] if keywords else [])
        hits = HybridSearchService().search(queries, keywords, filters, top_k=50, hard_cap=50,
                                            inferred_topic=heuristics.classify_topic(d["query"]) if not filters.topic else None)
        lang = response_language(None, detect_language(d["query"]), getattr(request.user, "preferred_language", None))
        outcome = ResearchOutcome(hits=hits, queries=queries, keywords=keywords, filters=filters)
        if request.user.is_authenticated:
            LegalResearchService.record(request.user, SearchKind.JUDGMENT, d["query"], outcome, lang)
        paginator, page = paginate_list(request, hits, view=self)
        resp = paginator.get_paginated_response([hit_to_dict(h, filters, lang) for h in page])
        resp.data["meta"].update({"query": d["query"], "filters": filters.as_dict(), "similarity_note": SIMILARITY_NOTE[lang],
                                  "data_freshness": "Results come from stored (cached) sources, not live court systems."})
        return resp


class JudgmentListView(APIView):
    """GET /api/v1/judgments/?state=&topic=&court=&q=&verification_status= — browse the stored corpus."""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Judgment.objects.select_related("court")
        p = request.query_params
        if p.get("state"):
            qs = qs.filter(state__iexact=p["state"])
        if p.get("topic"):
            qs = qs.filter(legal_topics__contains=[p["topic"]])
        if p.get("court"):
            qs = qs.filter(court__name__icontains=p["court"])
        if p.get("verification_status"):
            qs = qs.filter(verification_status=p["verification_status"].upper())
        if p.get("q"):
            qs = qs.filter(Q(title__icontains=p["q"]) | Q(citation__icontains=p["q"]) | Q(summary__icontains=p["q"]))
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(JudgmentListSerializer(page, many=True).data)


class JudgmentDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        j = Judgment.objects.select_related("court", "source").filter(pk=pk).first()
        if j is None:
            raise NotFoundError("The requested judgment could not be found.", code="JUDGMENT_NOT_FOUND")
        data = JudgmentSerializer(j).data
        data["source"] = ({"id": str(j.source_id), "verification_status": j.source.verification_status,
                           "retrieved_at": j.source.retrieved_at, "source_updated_at": j.source.source_updated_at}
                          if j.source else None)
        return Response(data)
