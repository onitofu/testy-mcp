class GetPlanTool:
    name = "get_plan"

    def execute(self, plan_id: int) -> dict:
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
