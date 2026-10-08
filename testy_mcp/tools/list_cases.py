from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.input_validation import InputValidation
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
        """List test cases with filters, count, pages and results; estimates are duration strings.

        Args:
            project_id: Project ID
            suite_id: Filter by suite
            search: Search by case name
            page: Page number starting at 1
            page_size: Records per page (default: 100, maximum: 1000)
        """
        pagination = Pagination(page, page_size)
        access = AccessControl()
        qs = access.list("case", project_id)
        if suite_id is not None:
            access.related("suite", suite_id, project_id)
            qs = qs.filter(suite_id=suite_id)
        if search:
            qs = qs.filter(name__icontains=search)
        cases = list(pagination.paginate(qs.select_related("suite")))
        labeled = access.case_labels(project_id, [c.id for c in cases])
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
                    "estimate": InputValidation.format_estimate(c.estimate),
                    "labels": labels_by_case.get(c.id, []),
                }
                for c in cases
            ]
        )
