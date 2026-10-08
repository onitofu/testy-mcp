from testy_mcp.services.project_access import ProjectAccess


class GetProjectTool:
    name = "get_project"

    def execute(self, project_id: int) -> dict:
        """Get project information and statistics, subject to TestY read permissions.

        Args:
            project_id: Project ID
        """
        project = ProjectAccess().get(project_id)
        stats = {}
        s = getattr(project, "projectstatistics", None)
        if s is not None:
            stats = {
                "cases_count": s.cases_count,
                "suites_count": s.suites_count,
                "tests_count": s.tests_count,
                "plans_count": s.plans_count,
            }
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "is_archive": project.is_archive,
            "statistics": stats,
        }
