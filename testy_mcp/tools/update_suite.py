from django.db import transaction

from testy_mcp.services.access_control import AccessControl


class UpdateSuiteTool:
    name = "update_suite"

    @transaction.atomic
    def execute(
        self,
        suite_id: int,
        name: str | None = None,
        description: str | None = None,
        parent_id: int | None = None,
    ) -> dict:
        """Update a test suite.

        Args:
            suite_id: Suite ID
            name: New name
            description: New description
            parent_id: New parent suite ID
        """
        access = AccessControl()
        suite = access.get("suite", suite_id, "update")
        if parent_id is not None:
            access.parent("suite", parent_id, suite.project_id, suite)
        if name is not None:
            suite.name = name
        if description is not None:
            suite.description = description
        if parent_id is not None:
            suite.parent_id = parent_id
        suite.save()
        return {
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "parent_id": suite.parent_id,
        }
