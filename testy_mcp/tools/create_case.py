from django.db import transaction

from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.case_labels import CaseLabels
from testy_mcp.services.input_validation import InputValidation


class CreateCaseTool:
    name = "create_case"

    @transaction.atomic
    def execute(
        self,
        project_id: int,
        suite_id: int,
        name: str,
        scenario: str = "",
        expected: str = "",
        setup: str = "",
        teardown: str = "",
        description: str = "",
        estimate: int | str | None = None,
        steps: list[dict] | None = None,
        label_ids: list[int] | None = None,
    ) -> dict:
        """Create a test case. Supports two modes: simple (scenario/expected) or multi-step.

        Args:
            project_id: Project ID
            suite_id: Suite ID to place the case in
            name: Test case name
            scenario: Test scenario text (used when steps is not provided)
            expected: Expected result (used when steps is not provided)
            setup: Preconditions
            teardown: Postconditions
            description: Description
            estimate: Integer minutes or a duration string ("30s", "1m 30s", "1d")
            steps: Array of steps for multi-step mode. Each:
                   {"name": str, "scenario": str, "expected": str}.
                   When provided, uses step-based format instead of single scenario.
            label_ids: Array of label IDs to attach to the case.
                       Use list_labels to get available IDs.
        """
        from testy.tests_description.models import TestCase, TestCaseStep

        access = AccessControl()
        access.create("case", project_id)
        access.related("suite", suite_id, project_id)
        access.related_many("label", label_ids or [], project_id)
        data = InputValidation.case(
            {
                "name": name,
                "scenario": scenario,
                "expected": expected,
                "setup": setup,
                "teardown": teardown,
                "description": description,
                "estimate": estimate,
                "steps": steps,
            }
        )
        steps = data.pop("steps")
        is_steps = bool(steps)
        if is_steps:
            data.update(scenario="", expected="")
        with transaction.atomic():
            case = TestCase.objects.create(
                project_id=project_id,
                suite_id=suite_id,
                is_steps=is_steps,
                **data,
            )
            if is_steps:
                for i, step in enumerate(steps):
                    TestCaseStep.objects.create(
                        project_id=project_id,
                        test_case=case,
                        name=step.get("name", f"Step {i + 1}"),
                        scenario=step.get("scenario", ""),
                        expected=step.get("expected", ""),
                        sort_order=i,
                    )
            if label_ids:
                CaseLabels.attach(case, label_ids)
        return {
            "id": case.id,
            "name": case.name,
            "suite_id": case.suite_id,
            "is_steps": case.is_steps,
        }
