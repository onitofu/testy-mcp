from django.db import transaction

from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.case_labels import CaseLabels
from testy_mcp.services.input_validation import InputValidation
from testy_mcp.services.optional_argument import OptionalArgument


class UpdateCaseTool:
    name = "update_case"

    @transaction.atomic
    def execute(
        self,
        case_id: int,
        name: str | None = None,
        suite_id: int | None = None,
        scenario: str | None = None,
        expected: str | None = None,
        setup: str | None = None,
        teardown: str | None = None,
        description: str | None = None,
        estimate: int | str | None = OptionalArgument.UNSET,
        steps: list[dict] | None = None,
        label_ids: list[int] | None = None,
    ) -> dict:
        """Update a test case. Can switch between simple and multi-step modes.

        Args:
            case_id: Test case ID
            name: New name
            suite_id: Move to another suite
            scenario: New test scenario (simple mode)
            expected: New expected result (simple mode)
            setup: New preconditions
            teardown: New postconditions
            description: New description
            estimate: Integer minutes or a duration string; null clears it, omission keeps it
            steps: Replace steps with new ones. Each:
                   {"name": str, "scenario": str, "expected": str}.
                   Pass empty list [] to switch to simple mode.
            label_ids: Replace labels. Pass array of label IDs.
                       Pass empty list [] to remove all labels.
        """
        from testy.tests_description.models import TestCase, TestCaseStep

        access = AccessControl()
        case = access.get("case", case_id, "update")
        if suite_id is not None:
            access.related("suite", suite_id, case.project_id)
        if label_ids is not None:
            access.related_many("label", label_ids, case.project_id)
        if steps is not None:
            access.case_steps(case)
            steps = InputValidation.case({"name": case.name, "steps": steps})["steps"]
        fields = {
            "name": name,
            "scenario": scenario,
            "expected": expected,
            "setup": setup,
            "teardown": teardown,
            "description": description,
        }
        fields = InputValidation.fields(
            TestCase, {key: value for key, value in fields.items() if value is not None}
        )
        if suite_id is not None:
            fields["suite_id"] = suite_id
        if estimate is not OptionalArgument.UNSET:
            fields["estimate"] = InputValidation.estimate(estimate)
        for field, value in fields.items():
            setattr(case, field, value)
        with transaction.atomic():
            if steps is not None:
                access.case_steps(case).update(is_deleted=True)
                if steps:
                    case.is_steps = True
                    case.scenario = ""
                    case.expected = ""
                    for i, step in enumerate(steps):
                        TestCaseStep.objects.create(
                            project_id=case.project_id,
                            test_case=case,
                            name=step.get("name", f"Step {i + 1}"),
                            scenario=step.get("scenario", ""),
                            expected=step.get("expected", ""),
                            sort_order=i,
                        )
                else:
                    case.is_steps = False
            if label_ids is not None:
                CaseLabels.sync(case, label_ids)
            case.save()
        return {
            "id": case.id,
            "name": case.name,
            "suite_id": case.suite_id,
            "is_steps": case.is_steps,
        }
