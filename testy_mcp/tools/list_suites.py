class ListSuitesTool:
    name = "list_suites"

    def execute(self, project_id: int, tree_view: bool = True, search: str = "") -> list[dict]:
        """List test suites in a project.

        Args:
            project_id: Project ID
            tree_view: Return as tree structure (default: True)
            search: Search by suite name
        """
        from testy.tests_description.models import TestSuite

        qs = TestSuite.objects.filter(project_id=project_id, is_deleted=False)
        if search:
            qs = qs.filter(name__icontains=search)
        suites = list(qs.values("id", "name", "description", "parent_id"))
        if not tree_view:
            return suites
        return self._build_tree(suites)

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
