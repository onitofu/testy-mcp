from testy_mcp.formatters.plan_results_json_formatter import PlanResultsJsonFormatter
from testy_mcp.formatters.plan_results_markdown_formatter import PlanResultsMarkdownFormatter


class ExportPlanResultsTool:
    name = "export_plan_results"

    def execute(self, plan_id: int, status: str | None = None, format: str = "markdown") -> str:
        """Export test plan results for AI analysis.

        Args:
            plan_id: Test plan ID
            status: Filter by status name (e.g. "Failed" to see only failures)
            format: "markdown" (default) or "json"
        """
        from django.db.models import Count
        from testy.tests_representation.models import Test, TestPlan

        plan = TestPlan.objects.get(id=plan_id, is_deleted=False)
        tests = Test.objects.filter(plan=plan, is_deleted=False).select_related(
            "case", "last_status", "assignee"
        )
        if status:
            tests = tests.filter(last_status__name__iexact=status)
        test_results = []
        for test in tests:
            latest_result = (
                test.results.select_related("status", "user").order_by("-created_at").first()
            )
            test_results.append((test, latest_result))
        all_tests = Test.objects.filter(plan=plan, is_deleted=False)
        stats = dict(
            all_tests.filter(last_status__isnull=False)
            .values_list("last_status__name")
            .annotate(count=Count("id"))
            .values_list("last_status__name", "count")
        )
        total = all_tests.count()
        untested = total - sum(stats.values())
        if untested > 0:
            stats["Untested"] = untested
        if format == "json":
            return PlanResultsJsonFormatter().format(plan, test_results, stats, total)
        return PlanResultsMarkdownFormatter().format(plan, test_results, stats, total)
