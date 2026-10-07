class ListProjectsTool:
    name = "list_projects"

    def execute(self, is_archive: bool = False, search: str = "") -> list[dict]:
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
            {"id": p.id, "name": p.name, "description": p.description, "is_archive": p.is_archive}
            for p in qs[:100]
        ]
