from testy_mcp.services.access_control import AccessControl


class ProjectOverviewResource:
    name = "project_overview"
    uri = "testy://project/{project_id}/overview"

    def execute(self, project_id: int) -> str:
        """Project overview: statistics and suite structure."""
        access = AccessControl()
        project = access.get("project", project_id)
        stats = {}
        if hasattr(project, "projectstatistics"):
            s = project.projectstatistics
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
        suites = list(access.list("suite", project_id))
        from django.db.models import Count

        case_counts = dict(
            access.list("case", project_id)
            .values("suite_id")
            .annotate(count=Count("id"))
            .values_list("suite_id", "count")
        )
        roots = [s for s in suites if s.parent_id is None]
        children_map = {}
        for s in suites:
            children_map.setdefault(s.parent_id, []).append(s)

        def render(suite, prefix="", is_last=True):
            connector = "└── " if is_last else "├── "
            count = case_counts.get(suite.id, 0)
            lines.append(f"{prefix}{connector}{suite.name} ({count} cases)")
            children = sorted(children_map.get(suite.id, []), key=lambda s: s.name)
            for i, child in enumerate(children):
                ext = "    " if is_last else "│   "
                render(child, prefix + ext, i == len(children) - 1)

        for i, root in enumerate(sorted(roots, key=lambda s: s.name)):
            render(root, "", i == len(roots) - 1)
        return "\n".join(lines)
