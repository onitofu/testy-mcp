import logging

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('testy_mcp')


def register(mcp: FastMCP):

    @mcp.tool()
    def list_projects(is_archive: bool = False, search: str = '') -> list[dict]:
        """List available TestY projects.

        Args:
            is_archive: Filter by archived projects (default: False)
            search: Search by project name
        """
        from testy.core.models import Project

        qs = Project.objects.filter(is_deleted=False, is_archive=is_archive)
        if search:
            qs = qs.filter(name__icontains=search)

        return [
            {
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'is_archive': p.is_archive,
            }
            for p in qs[:100]
        ]

    @mcp.tool()
    def get_project(project_id: int) -> dict:
        """Get detailed project information including statistics.

        Args:
            project_id: Project ID
        """
        from testy.core.models import Project

        project = Project.objects.get(id=project_id, is_deleted=False)
        stats = {}
        if hasattr(project, 'project_statistics'):
            s = project.project_statistics
            stats = {
                'cases_count': s.cases_count,
                'suites_count': s.suites_count,
                'tests_count': s.tests_count,
                'plans_count': s.plans_count,
            }

        return {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'is_archive': project.is_archive,
            'statistics': stats,
        }
