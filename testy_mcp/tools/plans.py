import logging

from django.db import transaction
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("testy_mcp")


def register(mcp: FastMCP):
    @mcp.tool()
    def list_plans(project_id: int, is_archive: bool = False, search: str = "") -> list[dict]:
        """List test plans in a project.

        Args:
            project_id: Project ID
            is_archive: Filter by archived plans (default: False)
            search: Search by plan name
        """
        from testy.tests_representation.models import TestPlan

        qs = TestPlan.objects.filter(project_id=project_id, is_deleted=False, is_archive=is_archive)
        if search:
            qs = qs.filter(name__icontains=search)

        return [
            {
                "id": p.id,
                "name": p.name,
                "started_at": p.started_at.isoformat() if p.started_at else None,
                "due_date": p.due_date.isoformat() if p.due_date else None,
                "finished_at": p.finished_at.isoformat() if p.finished_at else None,
                "is_archive": p.is_archive,
                "parent_id": p.parent_id,
            }
            for p in qs[:100]
        ]

    @mcp.tool()
    def get_plan(plan_id: int) -> dict:
        """Get test plan with statistics.

        Args:
            plan_id: Test plan ID
        """
        from django.db.models import Count
        from testy.tests_representation.models import Test, TestPlan

        plan = TestPlan.objects.get(id=plan_id, is_deleted=False)

        tests = Test.objects.filter(plan=plan, is_deleted=False)
        total = tests.count()

        status_counts = (
            tests.filter(last_status__isnull=False)
            .values("last_status__name")
            .annotate(count=Count("id"))
        )
        stats = {item["last_status__name"]: item["count"] for item in status_counts}

        untested = total - sum(stats.values())
        if untested > 0:
            stats["Untested"] = untested

        return {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "started_at": plan.started_at.isoformat() if plan.started_at else None,
            "due_date": plan.due_date.isoformat() if plan.due_date else None,
            "finished_at": plan.finished_at.isoformat() if plan.finished_at else None,
            "is_archive": plan.is_archive,
            "statistics": stats,
            "total_tests": total,
        }

    @mcp.tool()
    def create_plan(
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
                    Test.objects.create(
                        project_id=project_id,
                        case_id=case_id,
                        plan=plan,
                    )
                    tests_added += 1

        return {
            "id": plan.id,
            "name": plan.name,
            "tests_added": tests_added,
        }

    @mcp.tool()
    def add_tests_to_plan(plan_id: int, case_ids: list[int]) -> list[dict]:
        """Add test cases to an existing test plan.

        Args:
            plan_id: Test plan ID
            case_ids: Array of test case IDs to add
        """
        from testy.tests_representation.models import Test, TestPlan

        plan = TestPlan.objects.get(id=plan_id, is_deleted=False)
        created = []

        with transaction.atomic():
            for case_id in case_ids:
                test = Test.objects.create(
                    project_id=plan.project_id,
                    case_id=case_id,
                    plan=plan,
                )
                created.append(
                    {
                        "id": test.id,
                        "case_id": test.case_id,
                        "plan_id": test.plan_id,
                    }
                )

        return created

    @mcp.tool()
    def list_tests(
        plan_id: int,
        status: str | None = None,
        search: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List tests in a test plan with their current statuses.

        Args:
            plan_id: Test plan ID
            status: Filter by status name (e.g. "Passed", "Failed")
            search: Search by test case name
            limit: Max records (default: 50)
            offset: Pagination offset
        """
        from testy.tests_representation.models import Test

        qs = Test.objects.filter(plan_id=plan_id, is_deleted=False).select_related(
            "case", "last_status", "assignee"
        )
        if status:
            qs = qs.filter(last_status__name__iexact=status)
        if search:
            qs = qs.filter(case__name__icontains=search)

        total = qs.count()
        tests = qs[offset : offset + limit]

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "tests": [
                {
                    "id": t.id,
                    "case_id": t.case_id,
                    "case_name": t.case.name,
                    "assignee": t.assignee.username if t.assignee else None,
                    "last_status": t.last_status.name if t.last_status else "Untested",
                    "results_count": t.results.count(),
                }
                for t in tests
            ],
        }
