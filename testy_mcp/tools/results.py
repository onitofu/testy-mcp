import logging

from django.db import transaction
from mcp.server.fastmcp import FastMCP

from testy_mcp.context import get_current_user

logger = logging.getLogger("testy_mcp")

MAX_BULK_RESULTS = 500


def register(mcp: FastMCP):
    @mcp.tool()
    def submit_result(
        test_id: int,
        status: str,
        comment: str = "",
        execution_time: int | None = None,
    ) -> dict:
        """Submit a test execution result.

        Args:
            test_id: Test ID (test in a plan, not test case)
            status: Status name: "Passed", "Failed", "Skipped", "Blocked", "Broken", "Retest"
            comment: Result comment (Markdown)
            execution_time: Execution time in seconds
        """
        from testy.tests_representation.models import Test, TestResult

        test = Test.objects.select_related("case").get(id=test_id, is_deleted=False)
        status_obj = _resolve_status(status, test.project_id)
        user = get_current_user()

        result = TestResult.objects.create(
            project_id=test.project_id,
            test=test,
            status=status_obj,
            user=user,
            comment=comment,
            execution_time=execution_time,
            test_case_version=test.case.history.first().history_id
            if test.case.history.exists()
            else 0,
        )

        return {
            "id": result.id,
            "test_id": test_id,
            "status": status_obj.name,
            "comment": comment,
            "execution_time": execution_time,
            "created_at": result.created_at.isoformat(),
        }

    @mcp.tool()
    def submit_results_bulk(plan_id: int, results: list[dict]) -> dict:
        """Submit multiple test results in one atomic operation.

        Args:
            plan_id: Test plan ID
            results: Array of results. Each: {"test_id": int, "status": str,
                     "comment": str, "execution_time": int}
                     Alternative: {"case_name": str, "status": str, ...} to identify by case name.

        Maximum 500 results per call.
        """
        from testy.tests_representation.models import Test, TestResult

        if len(results) > MAX_BULK_RESULTS:
            raise ValueError(f"Maximum {MAX_BULK_RESULTS} results per call, got {len(results)}")

        plan_tests = Test.objects.filter(plan_id=plan_id, is_deleted=False).select_related("case")
        tests_by_id = {t.id: t for t in plan_tests}
        tests_by_name = {}
        for t in plan_tests:
            name = t.case.name.lower()
            if name in tests_by_name:
                tests_by_name[name] = None
            else:
                tests_by_name[name] = t

        user = get_current_user()
        submitted = []

        with transaction.atomic():
            for r in results:
                test = _resolve_test(r, tests_by_id, tests_by_name)
                status_obj = _resolve_status(r["status"], test.project_id)

                result = TestResult.objects.create(
                    project_id=test.project_id,
                    test=test,
                    status=status_obj,
                    user=user,
                    comment=r.get("comment", ""),
                    execution_time=r.get("execution_time"),
                    test_case_version=test.case.history.first().history_id
                    if test.case.history.exists()
                    else 0,
                )
                submitted.append(
                    {
                        "test_id": test.id,
                        "status": status_obj.name,
                        "result_id": result.id,
                    }
                )

        return {
            "submitted": len(submitted),
            "results": submitted,
        }


def _resolve_test(result_data: dict, tests_by_id: dict, tests_by_name: dict):
    if "test_id" in result_data:
        test_id = result_data["test_id"]
        if test_id not in tests_by_id:
            raise ValueError(f"Test with ID {test_id} not found in this plan")
        return tests_by_id[test_id]

    if "case_name" in result_data:
        name = result_data["case_name"].lower()
        test = tests_by_name.get(name)
        if test is None:
            if name in tests_by_name:
                raise ValueError(
                    f'Multiple tests found for case name "{result_data["case_name"]}". '
                    f"Use test_id instead."
                )
            raise ValueError(
                f'No test found for case name "{result_data["case_name"]}" in this plan'
            )
        return test

    raise ValueError('Each result must have either "test_id" or "case_name"')


def _resolve_status(status_name: str, project_id: int):
    from django.db.models import Q
    from testy.tests_representation.models import ResultStatus

    status = ResultStatus.objects.filter(
        Q(project_id=project_id) | Q(project_id__isnull=True),
        name__iexact=status_name,
        is_deleted=False,
    ).first()

    if not status:
        available = list(
            ResultStatus.objects.filter(
                Q(project_id=project_id) | Q(project_id__isnull=True),
                is_deleted=False,
            ).values_list("name", flat=True)
        )
        raise ValueError(f'Status "{status_name}" not found. Available: {available}')

    return status
