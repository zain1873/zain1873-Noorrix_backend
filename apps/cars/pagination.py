import math

from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


def _int_param(request, name, default):
    try:
        return int(request.query_params.get(name, default))
    except (TypeError, ValueError):
        return default


class OptionalPagePagination(BasePagination):
    """Page-number pagination that only kicks in when ``?page=`` is sent.

    Without ``page`` the view returns the plain array it always has (the
    chatbot, appointment form, home sections and brand pages rely on that).
    With it, the response is wrapped in count/page/next/previous/results.
    A page past the last one returns empty ``results`` rather than a 404.
    """

    page_query_param      = "page"
    page_size_query_param = "page_size"
    page_size             = 12
    max_page_size         = 48

    def paginate_queryset(self, queryset, request, view=None):
        if self.page_query_param not in request.query_params:
            return None

        self.request   = request
        self.page      = max(1, _int_param(request, self.page_query_param, 1))
        self.page_size = max(1, min(
            _int_param(request, self.page_size_query_param, self.page_size),
            self.max_page_size,
        ))
        self.count       = queryset.count()
        self.total_pages = max(1, math.ceil(self.count / self.page_size))

        start = (self.page - 1) * self.page_size
        return list(queryset[start:start + self.page_size])

    def _page_url(self, page):
        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.page_size_query_param, self.page_size)
        return replace_query_param(url, self.page_query_param, page)

    def get_paginated_response(self, data):
        has_next     = self.page < self.total_pages
        # From a page past the end, "previous" points at the real last page.
        previous     = min(self.page - 1, self.total_pages)
        return Response({
            "count":       self.count,
            "page":        self.page,
            "page_size":   self.page_size,
            "total_pages": self.total_pages,
            "next":        self._page_url(self.page + 1) if has_next else None,
            "previous":    self._page_url(previous) if self.page > 1 else None,
            "results":     data,
        })

    def get_paginated_response_schema(self, schema):
        nullable_url = {"type": "string", "format": "uri", "nullable": True}
        return {
            "type": "object",
            "required": ["count", "page", "page_size", "total_pages", "next", "previous", "results"],
            "properties": {
                "count":       {"type": "integer", "example": 57},
                "page":        {"type": "integer", "example": 1},
                "page_size":   {"type": "integer", "example": 12},
                "total_pages": {"type": "integer", "example": 5},
                "next":        nullable_url,
                "previous":    nullable_url,
                "results":     schema,
            },
        }

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": self.page_query_param, "in": "query", "required": False,
                "schema": {"type": "integer", "minimum": 1},
                "description": "Page number. Omit to get the full list as a plain array.",
            },
            {
                "name": self.page_size_query_param, "in": "query", "required": False,
                "schema": {"type": "integer", "minimum": 1, "maximum": self.max_page_size,
                           "default": self.page_size},
                "description": "Results per page (only used together with page).",
            },
        ]
