import logging

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("testy_mcp")


def register(mcp: FastMCP):
    @mcp.resource("testy://project/{project_id}/overview")
    def project_overview(project_id: int) -> str:
        """Project overview: statistics and suite structure."""
        from testy.core.models import Project
        from testy.tests_description.models import TestSuite

        project = Project.objects.get(id=project_id, is_deleted=False)
        stats = {}
        if hasattr(project, "project_statistics"):
            s = project.project_statistics
            stats = {
                "suites": s.suites_count,
                "cases": s.cases_count,
                "plans": s.plans_count,
                "tests": s.tests_count,
            }

        lines = [
            f"Project: {project.name}",
            f'Suites: {stats.get("suites", 0)}, Cases: {stats.get("cases", 0)}, '
            f'Plans: {stats.get("plans", 0)}',
            "",
            "Structure:",
        ]

        suites = list(TestSuite.objects.filter(project=project, is_deleted=False))
        from django.db.models import Count
        from testy.tests_description.models import TestCase

        case_counts = dict(
            TestCase.objects.filter(project=project, is_deleted=False)
            .values("suite_id")
            .annotate(count=Count("id"))
            .values_list("suite_id", "count")
        )

        roots = [s for s in suites if s.parent_id is None]
        children_map = {}
        for s in suites:
            children_map.setdefault(s.parent_id, []).append(s)

        def render(suite, prefix="", is_last=True):
            connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "
            count = case_counts.get(suite.id, 0)
            lines.append(f"{prefix}{connector}{suite.name} ({count} cases)")
            children = sorted(children_map.get(suite.id, []), key=lambda s: s.name)
            for i, child in enumerate(children):
                ext = "    " if is_last else "\u2502   "
                render(child, prefix + ext, i == len(children) - 1)

        for i, root in enumerate(sorted(roots, key=lambda s: s.name)):
            render(root, "", i == len(roots) - 1)

        return "\n".join(lines)

    @mcp.resource("testy://project/{project_id}/labels")
    def project_labels(project_id: int) -> str:
        """List of all project labels."""
        from testy.core.models import Label

        labels = Label.objects.filter(project_id=project_id, is_deleted=False)
        if not labels:
            return "No labels in this project."

        lines = ["Project labels:", ""]
        for label in labels:
            lines.append(f"- {label.name} (color: {label.color})")
        return "\n".join(lines)

    @mcp.resource("testy://project/{project_id}/statuses")
    def project_statuses(project_id: int) -> str:
        """List of available result statuses."""
        from django.db.models import Q
        from testy.tests_representation.models import ResultStatus

        statuses = ResultStatus.objects.filter(
            Q(project_id=project_id) | Q(project_id__isnull=True),
            is_deleted=False,
        )
        lines = ["Available result statuses:", ""]
        for s in statuses:
            stype = "system" if s.type == 0 else "custom"
            lines.append(f"- {s.name} ({stype}, color: {s.color})")
        return "\n".join(lines)
