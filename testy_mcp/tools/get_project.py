class GetProjectTool:
    name = "get_project"

    def execute(self, project_id: int) -> dict:
        """Get detailed project information including statistics.

        Args:
            project_id: Project ID
        """
        from testy.core.models import Project

        project = Project.objects.get(id=project_id, is_deleted=False)
        stats = {}
        if hasattr(project, "project_statistics"):
            s = project.project_statistics
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
