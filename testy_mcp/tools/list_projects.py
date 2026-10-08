from testy_mcp.services.pagination import Pagination
from testy_mcp.services.project_access import ProjectAccess


class ListProjectsTool:
    name = "list_projects"

    def execute(
        self, is_archive: bool = False, search: str = "", page: int = 1, page_size: int = 100
    ) -> dict:
        """List TestY projects the current user can read, with count, pages and results.

        Args:
            is_archive: False for active projects, True for archived projects only
            search: Search by project name
            page: Page number starting at 1
            page_size: Records per page (default: 100, maximum: 1000)
        """
        pagination = Pagination(page, page_size)
        qs = ProjectAccess().readable().filter(is_archive=is_archive)
        if search:
            qs = qs.filter(name__icontains=search)
        return pagination.response(
            [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "is_archive": p.is_archive,
                }
                for p in pagination.paginate(qs)
            ]
        )
