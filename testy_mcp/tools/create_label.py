from testy_mcp.context import RequestContext


class CreateLabelTool:
    name = "create_label"

    def execute(self, project_id: int, name: str, color: str = "#4A90D9") -> dict:
        """Create a label in a project.

        Args:
            project_id: Project ID
            name: Label name
            color: Color in hex (default: "#4A90D9")
        """
        from testy.core.models import Label

        label = Label.objects.create(
            project_id=project_id, name=name, color=color, user=RequestContext.get()
        )
        return {"id": label.id, "name": label.name, "color": label.color}
