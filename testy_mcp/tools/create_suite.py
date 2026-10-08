from django.db import transaction

from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.input_validation import InputValidation


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
        data = InputValidation.fields(TestSuite, {"name": name, "description": description})
        suite = TestSuite.objects.create(project_id=project_id, parent_id=parent_id, **data)
        return {
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "parent_id": suite.parent_id,
        }
