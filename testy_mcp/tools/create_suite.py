from django.db import transaction

from testy_mcp.services.access_control import AccessControl


class CreateSuiteTool:
    name = "create_suite"

    @transaction.atomic
    def execute(
        self, project_id: int, name: str, description: str = "", parent_id: int | None = None
    ) -> dict:
        """Create a test suite.

        Args:
            project_id: Project ID
            name: Suite name
            description: Suite description (supports Markdown)
            parent_id: Parent suite ID for nesting
        """
        from testy.tests_description.models import TestSuite

        access = AccessControl()
        access.create("suite", project_id)
        if parent_id is not None:
            access.parent("suite", parent_id, project_id)
        suite = TestSuite.objects.create(
            project_id=project_id, name=name, description=description, parent_id=parent_id
        )
        return {
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "parent_id": suite.parent_id,
        }
