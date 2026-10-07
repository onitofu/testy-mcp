class ProjectLabelsResource:
    name = "project_labels"
    uri = "testy://project/{project_id}/labels"

    def execute(self, project_id: int) -> str:
        """List of all project labels."""
        from testy.core.models import Label

        labels = Label.objects.filter(project_id=project_id, is_deleted=False)
        if not labels:
            return "No labels in this project."
        lines = ["Project labels:", ""]
        for label in labels:
            lines.append(f"- {label.name} (color: {label.color})")
        return "\n".join(lines)
