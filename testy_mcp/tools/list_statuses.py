from django.db.models import Q


class ListStatusesTool:
    name = "list_statuses"

    def execute(self, project_id: int) -> list[dict]:
        """List available result statuses (system and custom) for a project.

        Args:
            project_id: Project ID
        """
        from testy.tests_representation.models import ResultStatus

        statuses = ResultStatus.objects.filter(
            Q(project_id=project_id) | Q(project_id__isnull=True), is_deleted=False
        )
        return [
            {
                "id": s.id,
                "name": s.name,
                "color": s.color,
                "type": "system" if s.type == 0 else "custom",
            }
            for s in statuses
        ]
