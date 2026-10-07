class ListPlansTool:
    name = "list_plans"

    def execute(self, project_id: int, is_archive: bool = False, search: str = "") -> list[dict]:
        """List test plans in a project.

        Args:
            project_id: Project ID
            is_archive: Filter by archived plans (default: False)
            search: Search by plan name
        """
        from testy.tests_representation.models import TestPlan

        qs = TestPlan.objects.filter(project_id=project_id, is_deleted=False, is_archive=is_archive)
        if search:
            qs = qs.filter(name__icontains=search)
        return [
            {
                "id": p.id,
                "name": p.name,
                "started_at": p.started_at.isoformat() if p.started_at else None,
                "due_date": p.due_date.isoformat() if p.due_date else None,
                "finished_at": p.finished_at.isoformat() if p.finished_at else None,
                "is_archive": p.is_archive,
                "parent_id": p.parent_id,
            }
            for p in qs[:100]
        ]
