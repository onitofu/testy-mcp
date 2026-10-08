from django.db import transaction

from testy_mcp.services.access_control import AccessControl


class CreatePlanTool:
    name = "create_plan"

    @transaction.atomic
    def execute(
        self,
        project_id: int,
        name: str,
        started_at: str,
        due_date: str,
        description: str = "",
        parent_id: int | None = None,
        case_ids: list[int] | None = None,
    ) -> dict:
        """Create a test plan, optionally adding test cases to it.

        Args:
            project_id: Project ID
            name: Plan name
            started_at: Start date (ISO 8601, e.g. "2026-03-12")
            due_date: Due date (ISO 8601, e.g. "2026-03-19")
            description: Plan description
            parent_id: Parent plan ID
            case_ids: Test case IDs to add to the plan
        """
        from testy.tests_representation.models import Test, TestPlan

        access = AccessControl()
        access.create("plan", project_id)
        if parent_id is not None:
            access.parent("plan", parent_id, project_id)
        access.plan_cases(case_ids or [], project_id)
        with transaction.atomic():
            plan = TestPlan.objects.create(
                project_id=project_id,
                name=name,
                description=description,
                parent_id=parent_id,
                started_at=started_at,
                due_date=due_date,
            )
            tests_added = 0
            if case_ids:
                for case_id in case_ids:
                    Test.objects.create(project_id=project_id, case_id=case_id, plan=plan)
                    tests_added += 1
        return {"id": plan.id, "name": plan.name, "tests_added": tests_added}
