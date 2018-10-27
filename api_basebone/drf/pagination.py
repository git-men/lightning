from rest_framework.pagination import (
    _positive_int,
    PageNumberPagination as OriginPageNumberPagination
)
from rest_framework.response import Response


class PageNumberPagination(OriginPageNumberPagination):

    max_page_size = 1000
    page_size = 100
    page_query_param = 'page'
    page_size_query_param = 'size'

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                return _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                return
        return self.page_size
