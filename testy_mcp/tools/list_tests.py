class ListTestsTool:
    name = "list_tests"

    def execute(
        self,
        plan_id: int,
        status: str | None = None,
        search: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List tests in a test plan with their current statuses.

        Args:
            plan_id: Test plan ID
            status: Filter by status name (e.g. "Passed", "Failed")
            search: Search by test case name
            limit: Max records (default: 50)
            offset: Pagination offset
        """
        from testy.tests_representation.models import Test

        qs = Test.objects.filter(plan_id=plan_id, is_deleted=False).select_related(
            "case", "last_status", "assignee"
        )
        if status:
            qs = qs.filter(last_status__name__iexact=status)
        if search:
            qs = qs.filter(case__name__icontains=search)
        total = qs.count()
        tests = qs[offset : offset + limit]
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "tests": [
                {
                    "id": t.id,
                    "case_id": t.case_id,
                    "case_name": t.case.name,
                    "assignee": t.assignee.username if t.assignee else None,
                    "last_status": t.last_status.name if t.last_status else "Untested",
                    "results_count": t.results.count(),
                }
                for t in tests
            ],
        }
