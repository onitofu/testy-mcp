import logging

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('testy_mcp')


def register(mcp: FastMCP):

    @mcp.tool()
    def list_labels(project_id: int) -> list[dict]:
        """List labels in a project.

        Args:
            project_id: Project ID
        """
        from testy.core.models import Label

        return [
            {'id': l.id, 'name': l.name, 'color': l.color}
            for l in Label.objects.filter(project_id=project_id, is_deleted=False)
        ]

    @mcp.tool()
    def create_label(project_id: int, name: str, color: str = '#4A90D9') -> dict:
        """Create a label in a project.

        Args:
            project_id: Project ID
            name: Label name
            color: Color in hex (default: "#4A90D9")
        """
        from testy.core.models import Label
        from testy_mcp.context import get_current_user

        label = Label.objects.create(
            project_id=project_id,
            name=name,
            color=color,
            user=get_current_user(),
        )
        return {'id': label.id, 'name': label.name, 'color': label.color}
