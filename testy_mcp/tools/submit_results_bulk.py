from django.db import transaction

from testy_mcp.context import RequestContext
from testy_mcp.services.result_status_resolver import ResultStatusResolver


class SubmitResultsBulkTool:
    name = "submit_results_bulk"
    MAX_BULK_RESULTS = 500

    def execute(self, plan_id: int, results: list[dict]) -> dict:
        """Submit multiple test results in one atomic operation.

        Args:
            plan_id: Test plan ID
            results: Array of results. Each: {"test_id": int, "status": str,
                     "comment": str, "execution_time": int}
                     Alternative: {"case_name": str, "status": str, ...} to identify by case name.

        Maximum 500 results per call.
        """
        from testy.tests_representation.models import Test, TestResult

        if len(results) > self.MAX_BULK_RESULTS:
            raise ValueError(
                f"Maximum {self.MAX_BULK_RESULTS} results per call, got {len(results)}"
            )
        plan_tests = Test.objects.filter(plan_id=plan_id, is_deleted=False).select_related("case")
        tests_by_id = {t.id: t for t in plan_tests}
        tests_by_name = {}
        for t in plan_tests:
            name = t.case.name.lower()
            if name in tests_by_name:
                tests_by_name[name] = None
            else:
                tests_by_name[name] = t
        user = RequestContext.get()
        submitted = []
        with transaction.atomic():
            for r in results:
                test = self._resolve_test(r, tests_by_id, tests_by_name)
                status_obj = ResultStatusResolver.resolve(r["status"], test.project_id)
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
                    {"test_id": test.id, "status": status_obj.name, "result_id": result.id}
                )
        return {"submitted": len(submitted), "results": submitted}

    def _resolve_test(self, result_data: dict, tests_by_id: dict, tests_by_name: dict):
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
                    f"""No test found for case name "{result_data['case_name']}" in this plan"""
                )
            return test
        raise ValueError('Each result must have either "test_id" or "case_name"')
