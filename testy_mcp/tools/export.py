import logging

from mcp.server.fastmcp import FastMCP

from testy_mcp.formatters import (
    format_plan_results_json,
    format_plan_results_markdown,
    format_suite_json,
    format_suite_markdown,
)

logger = logging.getLogger("testy_mcp")


def register(mcp: FastMCP):
    @mcp.tool()
    def export_suite(suite_id: int, include_children: bool = True, format: str = "markdown") -> str:
        """Export all test cases in a suite in LLM-friendly format.

        Args:
            suite_id: Suite ID
            include_children: Include nested suites (default: True)
            format: "markdown" (default) or "json"
        """
        from testy.tests_description.models import TestCase, TestSuite

        suite = TestSuite.objects.get(id=suite_id, is_deleted=False)

        if include_children:
            all_suites = list(TestSuite.objects.filter(project=suite.project, is_deleted=False))
            descendant_ids = _get_descendant_ids(suite.id, all_suites)
            descendant_ids.add(suite.id)
        else:
            descendant_ids = {suite.id}

        suites = TestSuite.objects.filter(id__in=descendant_ids, is_deleted=False)
        cases = TestCase.objects.filter(
            suite_id__in=descendant_ids, is_deleted=False
        ).select_related("suite")

        if format == "json":
            return format_suite_json(suite, suites, cases)
        return format_suite_markdown(suite, suites, cases)

    @mcp.tool()
    def export_plan_results(
        plan_id: int, status: str | None = None, format: str = "markdown"
    ) -> str:
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
            return format_plan_results_json(plan, test_results, stats, total)
        return format_plan_results_markdown(plan, test_results, stats, total)


def _get_descendant_ids(suite_id: int, all_suites) -> set:
    children_map = {}
    for s in all_suites:
        pid = s.parent_id
        if pid not in children_map:
            children_map[pid] = []
        children_map[pid].append(s.id)

    result = set()
    stack = children_map.get(suite_id, [])
    while stack:
        sid = stack.pop()
        result.add(sid)
        stack.extend(children_map.get(sid, []))
    return result
