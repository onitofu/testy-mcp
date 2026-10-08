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
        from testy.core.models import Label

        pagination = Pagination(page, page_size)
        labels = Label.objects.filter(project_id=project_id, is_deleted=False)
        return pagination.response(
            [
                {"id": label.id, "name": label.name, "color": label.color}
                for label in pagination.paginate(labels)
            ]
        )
