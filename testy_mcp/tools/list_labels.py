from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.pagination import Pagination


class ListLabelsTool:
    name = "list_labels"

    def execute(self, project_id: int, page: int = 1, page_size: int = 100) -> dict:
        """List labels in a project, with count, pages and results.

        Args:
            project_id: Project ID
            page: Page number starting at 1
            page_size: Records per page (default: 100, maximum: 1000)
        """
        pagination = Pagination(page, page_size)
        labels = AccessControl().list("label", project_id)
        return pagination.response(
            [
                {"id": label.id, "name": label.name, "color": label.color}
                for label in pagination.paginate(labels)
            ]
        )
