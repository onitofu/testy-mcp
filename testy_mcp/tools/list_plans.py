from testy_mcp.services.pagination import Pagination


class ListPlansTool:
    name = "list_plans"

    def execute(
        self,
        project_id: int,
        is_archive: bool = False,
        search: str = "",
        page: int = 1,
        page_size: int = 100,
    ) -> dict:
        """List test plans in a project, with count, pages and results.

        Args:
            project_id: Project ID
            is_archive: False for active plans, True for archived plans only
            search: Search by plan name
            page: Page number starting at 1
            page_size: Records per page (default: 100, maximum: 1000)
        """
        from testy.tests_representation.models import TestPlan

        pagination = Pagination(page, page_size)
        qs = TestPlan.objects.filter(project_id=project_id, is_deleted=False, is_archive=is_archive)
        if search:
            qs = qs.filter(name__icontains=search)
        return pagination.response(
            [
                {
                    "id": p.id,
                    "name": p.name,
                    "started_at": p.started_at.isoformat() if p.started_at else None,
                    "due_date": p.due_date.isoformat() if p.due_date else None,
                    "finished_at": p.finished_at.isoformat() if p.finished_at else None,
                    "is_archive": p.is_archive,
                    "parent_id": p.parent_id,
                }
                for p in pagination.paginate(qs)
            ]
        )
