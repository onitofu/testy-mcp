class ListLabelsTool:
    name = "list_labels"

    def execute(self, project_id: int) -> list[dict]:
        """List labels in a project.

        Args:
            project_id: Project ID
        """
        from testy.core.models import Label

        return [
            {"id": label.id, "name": label.name, "color": label.color}
            for label in Label.objects.filter(project_id=project_id, is_deleted=False)
        ]
