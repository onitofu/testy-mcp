from django.db import transaction

from testy_mcp.services.case_labels import CaseLabels


class CreateCasesBulkTool:
    name = "create_cases_bulk"
    MAX_BULK_CASES = 100

    def execute(self, project_id: int, suite_id: int, cases: list[dict]) -> list[dict]:
        """Create multiple test cases in one atomic operation.

        Key tool for AI-driven test generation.

        Args:
            project_id: Project ID
            suite_id: Suite ID to place cases in
            cases: Array of test cases. Each: {"name": str, "scenario": str,
                   "expected": str, "setup": str, "teardown": str, "description": str,
                   "estimate": int, "steps": [{"name": str, "scenario": str,
                   "expected": str}], "label_ids": [int]}.
                   When "steps" is provided, the case uses step-based format.
                   "label_ids" attaches labels.

        Maximum 100 cases per call.
        """
        from testy.tests_description.models import TestCase, TestCaseStep

        if len(cases) > self.MAX_BULK_CASES:
            raise ValueError(f"Maximum {self.MAX_BULK_CASES} cases per call, got {len(cases)}")
        created = []
        with transaction.atomic():
            for case_data in cases:
                steps_data = case_data.get("steps")
                is_steps = bool(steps_data)
                case = TestCase.objects.create(
                    project_id=project_id,
                    suite_id=suite_id,
                    name=case_data["name"],
                    scenario="" if is_steps else case_data.get("scenario", ""),
                    expected="" if is_steps else case_data.get("expected", ""),
                    setup=case_data.get("setup", ""),
                    teardown=case_data.get("teardown", ""),
                    description=case_data.get("description", ""),
                    estimate=case_data.get("estimate"),
                    is_steps=is_steps,
                )
                if is_steps:
                    for i, step in enumerate(steps_data):
                        TestCaseStep.objects.create(
                            project_id=project_id,
                            test_case=case,
                            name=step.get("name", f"Step {i + 1}"),
                            scenario=step.get("scenario", ""),
                            expected=step.get("expected", ""),
                            sort_order=i,
                        )
                case_label_ids = case_data.get("label_ids")
                if case_label_ids:
                    CaseLabels.attach(case, case_label_ids)
                created.append({"id": case.id, "name": case.name, "is_steps": is_steps})
        return created
