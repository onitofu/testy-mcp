from django.db import transaction

from testy_mcp.services.access_control import AccessControl


class AddTestsToPlanTool:
    name = "add_tests_to_plan"

    @transaction.atomic
    def execute(self, plan_id: int, case_ids: list[int]) -> list[dict]:
        """Add test cases to an existing test plan.

        Args:
            plan_id: Test plan ID
            case_ids: Array of test case IDs to add
        """
        from testy.tests_representation.models import Test

        access = AccessControl()
        plan = access.plan_for_tests(plan_id)
        access.plan_cases(case_ids, plan.project_id)
        created = []
        with transaction.atomic():
            for case_id in case_ids:
                test = Test.objects.create(project_id=plan.project_id, case_id=case_id, plan=plan)
                created.append({"id": test.id, "case_id": test.case_id, "plan_id": test.plan_id})
        return created
