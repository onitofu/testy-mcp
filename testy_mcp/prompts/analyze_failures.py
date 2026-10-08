from mcp.server.fastmcp.prompts import base

from testy_mcp.services.access_control import AccessControl


class AnalyzeFailuresPrompt:
    name = "analyze_failures"

    def execute(self, plan_id: int) -> list[base.Message]:
        """Analyze failed tests in a test plan.

        Args:
            plan_id: Test plan ID
        """
        failures_info = ""
        access = AccessControl()
        plan = access.get("plan", plan_id)
        failed_tests = (
            access.tests(plan)
            .filter(last_status__name__iexact="failed")
            .select_related("case", "last_status")
        )
        lines = []
        for t in failed_tests[:50]:
            result = (
                access.results(t).select_related("status", "user").order_by("-created_at").first()
            )
            comment = result.comment if result else ""
            lines.append(f"- TC-{t.case_id}: {t.case.name}\n  Comment: {comment}")
        failures_info = "\n".join(lines) if lines else "(no failed tests)"
        return [
            base.UserMessage(
                content=f"""Analyze the failed tests in the test plan (ID={plan_id}):

{failures_info}

For each failed test:
1. Identify the probable cause of failure
2. Classify: product bug / test issue / infrastructure problem
3. Suggest actions

Group by probable root causes."""
            )
        ]
