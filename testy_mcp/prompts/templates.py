import logging

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

logger = logging.getLogger("testy_mcp")


def register(mcp: FastMCP):
    @mcp.prompt()
    def generate_cases(
        feature: str, suite_id: int, coverage_level: str = "standard"
    ) -> list[base.Message]:
        """Generate test cases for a feature description.

        Args:
            feature: Feature description to generate tests for
            suite_id: Target suite ID
            coverage_level: "smoke", "standard", or "full"
        """
        existing = ""
        labels_info = ""
        try:
            from testy.tests_description.models import TestCase, TestSuite

            suite = TestSuite.objects.get(id=suite_id, is_deleted=False)
            cases = TestCase.objects.filter(suite=suite, is_deleted=False)
            if cases.exists():
                existing = "\n".join(f"- {c.name}" for c in cases[:50])
            else:
                existing = "(no existing cases)"

            from testy.core.models import Label

            labels = Label.objects.filter(project=suite.project, is_deleted=False)
            if labels.exists():
                labels_info = ", ".join(f"{label.name} (id={label.id})" for label in labels)
            else:
                labels_info = "(no labels)"
        except Exception:
            existing = "(could not load)"
            labels_info = "(could not load)"

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
            ),
        ]

    @mcp.prompt()
    def analyze_failures(plan_id: int) -> list[base.Message]:
        """Analyze failed tests in a test plan.

        Args:
            plan_id: Test plan ID
        """
        failures_info = ""
        try:
            from testy.tests_representation.models import Test, TestPlan

            plan = TestPlan.objects.get(id=plan_id, is_deleted=False)
            failed_tests = Test.objects.filter(
                plan=plan,
                is_deleted=False,
                last_status__name__iexact="failed",
            ).select_related("case", "last_status")

            lines = []
            for t in failed_tests[:50]:
                result = t.results.select_related("status", "user").order_by("-created_at").first()
                comment = result.comment if result else ""
                lines.append(f"- TC-{t.case_id}: {t.case.name}\n  Comment: {comment}")
            failures_info = "\n".join(lines) if lines else "(no failed tests)"
        except Exception:
            failures_info = "(could not load)"

        return [
            base.UserMessage(
                content=f"""Analyze the failed tests in the test plan (ID={plan_id}):

{failures_info}

For each failed test:
1. Identify the probable cause of failure
2. Classify: product bug / test issue / infrastructure problem
3. Suggest actions

Group by probable root causes."""
            ),
        ]

    @mcp.prompt()
    def review_coverage(suite_id: int, requirements: str = "") -> list[base.Message]:
        """Analyze test coverage completeness for a suite.

        Args:
            suite_id: Suite ID to analyze
            requirements: Requirements description to compare against
        """
        cases_info = ""
        try:
            from testy.tests_description.models import TestCase, TestSuite

            suite = TestSuite.objects.get(id=suite_id, is_deleted=False)
            cases = TestCase.objects.filter(suite=suite, is_deleted=False)
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
        except Exception:
            cases_info = "(could not load)"

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
            ),
        ]
