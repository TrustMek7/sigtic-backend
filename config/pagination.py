from rest_framework.pagination import PageNumberPagination


class FlexPageNumberPagination(PageNumberPagination):
    """Paginación que acepta ?page_size= con máximo 100."""
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100
