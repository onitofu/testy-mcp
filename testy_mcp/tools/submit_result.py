from django.db import transaction

from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.result_status_resolver import ResultStatusResolver


class SubmitResultTool:
    name = "submit_result"

    @transaction.atomic
    def execute(
        self, test_id: int, status: str, comment: str = "", execution_time: int | None = None
    ) -> dict:
        """Submit a test execution result.

        Args:
            test_id: Test ID (test in a plan, not test case)
            status: Status name: "Passed", "Failed", "Skipped", "Blocked", "Broken", "Retest"
            comment: Result comment (Markdown)
            execution_time: Execution time in seconds
        """
        from testy.tests_representation.models import TestResult

        access = AccessControl()
        test = access.test_for_result(test_id)
        status_obj = ResultStatusResolver.resolve(status, test.project_id)
        user = access.user
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
