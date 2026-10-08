from django.db import transaction

from testy_mcp.services.access_control import AccessControl


class CreateLabelTool:
    name = "create_label"

    @transaction.atomic
    def execute(self, project_id: int, name: str, color: str = "#4A90D9") -> dict:
        """Create a label in a project.

        Args:
            project_id: Project ID
            name: Label name
            color: Color in hex (default: "#4A90D9")
        """
        from testy.core.models import Label

        access = AccessControl()
        access.create("label", project_id)
        label = Label.objects.create(
            project_id=project_id, name=name, color=color, user=access.user
        )
        return {"id": label.id, "name": label.name, "color": label.color}
