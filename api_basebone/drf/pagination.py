from rest_framework.pagination import PageNumberPagination as OriginPageNumberPagination
from rest_framework.response import Response


class PageNumberPagination(OriginPageNumberPagination):

    max_page_size = 1000
    page_size = 100
    page_query_param = 'page'
    page_size_query_param = 'size'
