import logging

from django.db.models import Count, Q
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('testy_mcp')


def register(mcp: FastMCP):

    @mcp.tool()
    def list_statuses(project_id: int) -> list[dict]:
        """List available result statuses (system and custom) for a project.

        Args:
            project_id: Project ID
        """
        from testy.tests_representation.models import ResultStatus

        statuses = ResultStatus.objects.filter(
            Q(project_id=project_id) | Q(project_id__isnull=True),
            is_deleted=False,
        )
        return [
            {
                'id': s.id,
                'name': s.name,
                'color': s.color,
                'type': 'system' if s.type == 0 else 'custom',
            }
            for s in statuses
        ]

    @mcp.tool()
    def get_plan_statistics(plan_id: int) -> dict:
        """Get test plan statistics: status distribution, pass rate, completion rate.

        Args:
            plan_id: Test plan ID
        """
        from testy.tests_representation.models import TestPlan, Test

        plan = TestPlan.objects.get(id=plan_id, is_deleted=False)
        tests = Test.objects.filter(plan=plan, is_deleted=False)
        total = tests.count()

        if total == 0:
            return {
                'plan_id': plan.id,
                'plan_name': plan.name,
                'total': 0,
                'by_status': {},
                'pass_rate': 0.0,
                'completion_rate': 0.0,
            }

        status_counts = dict(
            tests.filter(last_status__isnull=False)
            .values_list('last_status__name')
            .annotate(count=Count('id'))
            .values_list('last_status__name', 'count')
        )

        tested = sum(status_counts.values())
        untested = total - tested
        if untested > 0:
            status_counts['Untested'] = untested

        passed = status_counts.get('Passed', 0)
        pass_rate = round((passed / total) * 100, 1) if total else 0.0
        completion_rate = round((tested / total) * 100, 1) if total else 0.0

        return {
            'plan_id': plan.id,
            'plan_name': plan.name,
            'total': total,
            'by_status': status_counts,
            'pass_rate': pass_rate,
            'completion_rate': completion_rate,
        }
