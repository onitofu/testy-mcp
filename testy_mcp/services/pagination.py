from django.core.paginator import InvalidPage, Paginator
from django.db.models import QuerySet
from rest_framework.exceptions import NotFound, ValidationError


class Pagination:
    def __init__(self, page: int = 1, page_size: int = 100):
        if type(page) is not int or page < 1:
            raise ValidationError({"page": "Must be a positive integer."})
        if type(page_size) is not int or not 1 <= page_size <= 1000:
            raise ValidationError({"page_size": "Must be an integer between 1 and 1000."})
        self.number = page
        self.size = page_size
        self._page = None

    @staticmethod
    def order_queryset(queryset):
        ordering = queryset.query.order_by or (
            queryset.model._meta.ordering if queryset.query.default_ordering else ()
        )
        ordering = ordering or ()
        if not any(
            isinstance(field, str) and field.lstrip("-") in {"id", "pk"} for field in ordering
        ):
            ordering = (*ordering, "id")
        return queryset.order_by(*ordering)

    def paginate(self, objects):
        if isinstance(objects, QuerySet):
            objects = self.order_queryset(objects)
        try:
            self._page = Paginator(objects, self.size).page(self.number)
        except InvalidPage as exc:
            raise NotFound("Invalid page.") from exc
        return self._page

    def response(self, results: list[dict]) -> dict:
        return {
            "count": self._page.paginator.count,
            "pages": {
                "current": self._page.number,
                "total": self._page.paginator.num_pages,
                "next": self._page.next_page_number() if self._page.has_next() else None,
                "previous": self._page.previous_page_number()
                if self._page.has_previous()
                else None,
            },
            "results": results,
        }
