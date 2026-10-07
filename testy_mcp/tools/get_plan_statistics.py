from django.db.models import Count


class GetPlanStatisticsTool:
    name = "get_plan_statistics"

    def execute(self, plan_id: int) -> dict:
        """Get test plan statistics: status distribution, pass rate, completion rate.

        Args:
            plan_id: Test plan ID
        """
        from testy.tests_representation.models import Test, TestPlan

        plan = TestPlan.objects.get(id=plan_id, is_deleted=False)
        tests = Test.objects.filter(plan=plan, is_deleted=False)
        total = tests.count()
        if total == 0:
            return {
                "plan_id": plan.id,
                "plan_name": plan.name,
                "total": 0,
                "by_status": {},
                "pass_rate": 0.0,
                "completion_rate": 0.0,
            }
        status_counts = dict(
            tests.filter(last_status__isnull=False)
            .values_list("last_status__name")
            .annotate(count=Count("id"))
            .values_list("last_status__name", "count")
        )
        tested = sum(status_counts.values())
        untested = total - tested
        if untested > 0:
            status_counts["Untested"] = untested
        passed = status_counts.get("Passed", 0)
        pass_rate = round(passed / total * 100, 1) if total else 0.0
        completion_rate = round(tested / total * 100, 1) if total else 0.0
        return {
            "plan_id": plan.id,
            "plan_name": plan.name,
            "total": total,
            "by_status": status_counts,
            "pass_rate": pass_rate,
            "completion_rate": completion_rate,
        }
