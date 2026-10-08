from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.pagination import Pagination


class ListStatusesTool:
    name = "list_statuses"

    def execute(self, project_id: int, page: int = 1, page_size: int = 100) -> dict:
        """List system and custom project statuses, with count, pages and results.

        Args:
            project_id: Project ID
            page: Page number starting at 1
            page_size: Records per page (default: 100, maximum: 1000)
        """
        pagination = Pagination(page, page_size)
        statuses = AccessControl().list("status", project_id)
        return pagination.response(
            [
                {
                    "id": s.id,
                    "name": s.name,
                    "color": s.color,
                    "type": "system" if s.type == 0 else "custom",
                }
                for s in pagination.paginate(statuses)
            ]
        )
