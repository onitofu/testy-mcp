from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.input_validation import InputValidation


class GetCaseTool:
    name = "get_case"

    def execute(self, case_id: int) -> dict:
        """Get full test case content, with estimate as a TestY duration string or null.

        Args:
            case_id: Test case ID
        """
        access = AccessControl()
        c = access.get("case", case_id)
        labels = []
        for li in access.case_labels(c.project_id, [c.pk]):
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
                for s in access.case_steps(c).order_by("sort_order", "id")
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
            "estimate": InputValidation.format_estimate(c.estimate),
            "is_steps": c.is_steps,
            "labels": labels,
            "steps": steps,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
