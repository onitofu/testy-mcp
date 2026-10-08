from testy_mcp.services.pagination import Pagination


class ListCasesTool:
    name = "list_cases"

    def execute(
        self,
        project_id: int,
        suite_id: int | None = None,
        search: str = "",
        page: int = 1,
        page_size: int = 100,
    ) -> dict:
        """List test cases with filters, count, pages and results.

        Args:
            project_id: Project ID
            suite_id: Filter by suite
            search: Search by case name
            page: Page number starting at 1
            page_size: Records per page (default: 100, maximum: 1000)
        """
        from django.contrib.contenttypes.models import ContentType
        from testy.core.models import LabeledItem
        from testy.tests_description.models import TestCase

        pagination = Pagination(page, page_size)
        qs = TestCase.objects.filter(project_id=project_id, is_deleted=False)
        if suite_id:
            qs = qs.filter(suite_id=suite_id)
        if search:
            qs = qs.filter(name__icontains=search)
        cases = list(pagination.paginate(qs.select_related("suite")))
        ct = ContentType.objects.get_for_model(TestCase)
        labeled = LabeledItem.objects.filter(
            content_type=ct, object_id__in=[c.id for c in cases], is_deleted=False
        ).select_related("label")
        labels_by_case = {}
        for li in labeled:
            labels_by_case.setdefault(li.object_id, []).append(
                {"id": li.label_id, "name": li.label.name}
            )
        return pagination.response(
            [
                {
                    "id": c.id,
                    "name": c.name,
                    "suite_id": c.suite_id,
                    "suite_name": c.suite.name,
                    "is_steps": c.is_steps,
                    "estimate": c.estimate,
                    "labels": labels_by_case.get(c.id, []),
                }
                for c in cases
            ]
        )
