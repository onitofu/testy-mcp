from testy_mcp.services.pagination import Pagination


class ListTestsTool:
    name = "list_tests"

    def execute(
        self,
        plan_id: int,
        status: str | None = None,
        search: str = "",
        page: int = 1,
        page_size: int = 100,
    ) -> dict:
        """List tests and current statuses in a plan, with count, pages and results.

        Args:
            plan_id: Test plan ID
            status: Filter by status name (e.g. "Passed", "Failed")
            search: Search by test case name
            page: Page number starting at 1
            page_size: Records per page (default: 100, maximum: 1000)
        """
        from testy.tests_representation.models import Test

        pagination = Pagination(page, page_size)
        qs = Test.objects.filter(plan_id=plan_id, is_deleted=False).select_related(
            "case", "last_status", "assignee"
        )
        if status:
            qs = qs.filter(last_status__name__iexact=status)
        if search:
            qs = qs.filter(case__name__icontains=search)
        tests = pagination.paginate(qs)
        return pagination.response(
            [
                {
                    "id": t.id,
                    "case_id": t.case_id,
                    "case_name": t.case.name,
                    "assignee": t.assignee.username if t.assignee else None,
                    "last_status": t.last_status.name if t.last_status else "Untested",
                    "results_count": t.results.count(),
                }
                for t in tests
            ]
        )
