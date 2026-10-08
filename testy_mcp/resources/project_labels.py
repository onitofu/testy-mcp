from testy_mcp.services.access_control import AccessControl


class ProjectLabelsResource:
    name = "project_labels"
    uri = "testy://project/{project_id}/labels"

    def execute(self, project_id: int) -> str:
        """List of all project labels."""
        labels = AccessControl().list("label", project_id)
        if not labels:
            return "No labels in this project."
        lines = ["Project labels:", ""]
        for label in labels:
            lines.append(f"- {label.name} (color: {label.color})")
        return "\n".join(lines)
