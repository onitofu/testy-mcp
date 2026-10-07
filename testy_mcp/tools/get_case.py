class GetCaseTool:
    name = "get_case"

    def execute(self, case_id: int) -> dict:
        """Get full test case content.

        Args:
            case_id: Test case ID
        """
        from testy.tests_description.models import TestCase

        c = TestCase.objects.select_related("suite").get(id=case_id, is_deleted=False)
        labels = []
        for li in c.labeled_items.select_related("label").all():
            if hasattr(li, "label") and li.label:
                labels.append({"id": li.label.id, "name": li.label.name})
        steps = []
        if c.is_steps:
            steps = [
                {
                    "id": s.id,
                    "name": s.name,
                    "scenario": s.scenario,
                    "expected": s.expected,
                    "sort_order": s.sort_order,
                }
                for s in c.steps.filter(is_deleted=False).order_by("sort_order", "id")
            ]
        return {
            "id": c.id,
            "name": c.name,
            "suite": {"id": c.suite_id, "name": c.suite.name},
            "setup": c.setup,
            "scenario": c.scenario,
            "expected": c.expected,
            "teardown": c.teardown,
            "description": c.description,
            "estimate": c.estimate,
            "is_steps": c.is_steps,
            "labels": labels,
            "steps": steps,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
