from mcp.server.fastmcp.prompts import base

from testy_mcp.services.access_control import AccessControl


class ReviewCoveragePrompt:
    name = "review_coverage"

    def execute(self, suite_id: int, requirements: str = "") -> list[base.Message]:
        """Analyze test coverage completeness for a suite.

        Args:
            suite_id: Suite ID to analyze
            requirements: Requirements description to compare against
        """
        cases_info = ""
        access = AccessControl()
        suite = access.get("suite", suite_id)
        cases = access.list("case", suite.project_id).filter(suite_id=suite.pk)
        if cases.exists():
            lines = []
            for c in cases[:100]:
                lines.append(
                    f"### {c.name}\n- Setup: {c.setup}\n"
                    f"- Steps: {c.scenario}\n- Expected: {c.expected}"
                )
            cases_info = "\n\n".join(lines)
        else:
            cases_info = "(no test cases in this suite)"
        reqs_section = f"\nRequirements:\n{requirements}" if requirements else ""
        return [
            base.UserMessage(
                content=f"""Analyze test coverage of the suite (ID={suite_id}):

{cases_info}
{reqs_section}

Identify:
1. Which scenarios are covered
2. Which scenarios are missing (negative, edge cases, load testing)
3. Suggest missing test cases

If suggesting new cases, use create_cases_bulk tool to create them in suite_id={suite_id}."""
            )
        ]
