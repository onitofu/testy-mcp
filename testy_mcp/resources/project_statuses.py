class ProjectStatusesResource:
    name = "project_statuses"
    uri = "testy://project/{project_id}/statuses"

    def execute(self, project_id: int) -> str:
        """List of available result statuses."""
        from django.db.models import Q
        from testy.tests_representation.models import ResultStatus

        statuses = ResultStatus.objects.filter(
            Q(project_id=project_id) | Q(project_id__isnull=True), is_deleted=False
        )
        lines = ["Available result statuses:", ""]
        for s in statuses:
            stype = "system" if s.type == 0 else "custom"
            lines.append(f"- {s.name} ({stype}, color: {s.color})")
        return "\n".join(lines)
