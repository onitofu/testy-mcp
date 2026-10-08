from mcp.server.fastmcp.prompts import base

from testy_mcp.services.access_control import AccessControl


class GenerateCasesPrompt:
    name = "generate_cases"

    def execute(
        self, feature: str, suite_id: int, coverage_level: str = "standard"
    ) -> list[base.Message]:
        """Generate test cases for a feature description.

        Args:
            feature: Feature description to generate tests for
            suite_id: Target suite ID
            coverage_level: "smoke", "standard", or "full"
        """
        existing = ""
        labels_info = ""
        access = AccessControl()
        suite = access.get("suite", suite_id)
        cases = access.list("case", suite.project_id).filter(suite_id=suite.pk)
        if cases.exists():
            existing = "\n".join((f"- {c.name}" for c in cases[:50]))
        else:
            existing = "(no existing cases)"
        labels = access.list("label", suite.project_id)
        if labels.exists():
            labels_info = ", ".join((f"{label.name} (id={label.id})" for label in labels))
        else:
            labels_info = "(no labels)"
        return [
            base.UserMessage(
                content=f"""You are a QA engineer. Generate test cases for the following feature:

{feature}

Coverage level: {coverage_level}

Existing tests in suite (do not duplicate):
{existing}

Available labels: {labels_info}

For each test case provide: name, setup, scenario, expected, estimate (minutes).
After generation, use the create_cases_bulk tool to create the cases in suite_id={suite_id}."""
            )
        ]
