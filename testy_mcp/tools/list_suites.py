from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.pagination import Pagination


class ListSuitesTool:
    name = "list_suites"

    def execute(
        self,
        project_id: int,
        tree_view: bool = True,
        search: str = "",
        page: int = 1,
        page_size: int = 100,
    ) -> dict:
        """List test suites in a project, with count, pages and results.

        Args:
            project_id: Project ID
            tree_view: Paginate roots with complete filtered subtrees (default: True)
            search: Search by suite name
            page: Page number starting at 1
            page_size: Suites per page, or roots in tree view (default: 100, maximum: 1000)
        """
        pagination = Pagination(page, page_size)
        qs = AccessControl().list("suite", project_id)
        if search:
            qs = qs.filter(name__icontains=search)
        suites = pagination.order_queryset(qs).values("id", "name", "description", "parent_id")
        if not tree_view:
            return pagination.response(list(pagination.paginate(suites)))
        roots = self._build_tree(list(suites))
        return pagination.response(list(pagination.paginate(roots)))

    def _build_tree(self, suites: list[dict]) -> list[dict]:
        by_id = {s["id"]: {**s, "children": []} for s in suites}
        roots = []
        for s in by_id.values():
            parent = s.get("parent_id")
            if parent and parent in by_id:
                by_id[parent]["children"].append(s)
            else:
                roots.append(s)
        return roots
