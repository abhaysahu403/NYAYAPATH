from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "data": data,
            "meta": {
                "pagination": {
                    "count": self.page.paginator.count,
                    "page": self.page.number,
                    "page_size": self.get_page_size(self.request),
                    "total_pages": self.page.paginator.num_pages,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                }
            },
        })

    def get_paginated_response_schema(self, schema):
        return {"type": "object", "properties": {"success": {"type": "boolean"}, "data": schema, "meta": {"type": "object"}}}


def paginate_list(request, items, view=None):
    """Paginate an in-memory list (e.g. ranked search hits) with the standard envelope."""
    paginator = StandardPagination()
    page = paginator.paginate_queryset(items, request, view=view)
    return paginator, page
