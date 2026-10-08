from django.db import transaction
from rest_framework.exceptions import ValidationError

from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.result_status_resolver import ResultStatusResolver


class SubmitResultsBulkTool:
    name = "submit_results_bulk"
    MAX_BULK_RESULTS = 500

    @transaction.atomic
    def execute(self, plan_id: int, results: list[dict]) -> dict:
        """Submit multiple test results in one atomic operation.

        Args:
            plan_id: Test plan ID
            results: Array of results. Each: {"test_id": int, "status": str,
                     "comment": str, "execution_time": int}
                     Alternative: {"case_name": str, "status": str, ...} to identify by case name.

        Maximum 500 results per call.
        """
        from testy.tests_representation.models import TestResult

        if len(results) > self.MAX_BULK_RESULTS:
            raise ValidationError(
                f"Maximum {self.MAX_BULK_RESULTS} results per call, got {len(results)}"
            )
        if not results:
            raise ValidationError("At least one result is required.")
        access = AccessControl()
        plan, plan_tests = access.plan_for_results(plan_id)
        tests_by_id = {t.id: t for t in plan_tests}
        tests_by_name = {}
        for t in plan_tests:
            name = t.case.name.lower()
            if name in tests_by_name:
                tests_by_name[name] = None
            else:
                tests_by_name[name] = t
        user = access.user
        prepared = []
        for r in results:
            test = self._resolve_test(r, tests_by_id, tests_by_name)
            access.submit(test)
            status_obj = ResultStatusResolver.resolve(r["status"], test.project_id)
            prepared.append((r, test, status_obj))
        submitted = []
        with transaction.atomic():
            for r, test, status_obj in prepared:
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
                raise ValidationError(f"Test with ID {test_id} not found in this plan")
            return tests_by_id[test_id]
        if "case_name" in result_data:
            name = result_data["case_name"].lower()
            test = tests_by_name.get(name)
            if test is None:
                if name in tests_by_name:
                    raise ValidationError(
                        f'Multiple tests found for case name "{result_data["case_name"]}". '
                        f"Use test_id instead."
                    )
                raise ValidationError(
                    f"""No test found for case name "{result_data['case_name']}" in this plan"""
                )
            return test
        raise ValidationError('Each result must have either "test_id" or "case_name"')
