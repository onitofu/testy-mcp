from django.db import transaction

from testy_mcp.services.access_control import AccessControl
from testy_mcp.services.input_validation import InputValidation
from testy_mcp.services.optional_argument import OptionalArgument


class UpdateSuiteTool:
    name = "update_suite"

    @transaction.atomic
    def execute(
        self,
        suite_id: int,
        name: str | None = None,
        description: str | None = None,
        parent_id: int | None = OptionalArgument.UNSET,
    ) -> dict:
        """Update a test suite.

        Args:
            suite_id: Suite ID
            name: New name
            description: New description
            parent_id: New parent suite ID; null removes it, omission keeps it
        """
        from testy.tests_description.models import TestSuite

        access = AccessControl()
        suite = access.get("suite", suite_id, "update")
        if parent_id is not OptionalArgument.UNSET and parent_id is not None:
            access.parent("suite", parent_id, suite.project_id, suite)
        fields = {"name": name, "description": description}
        for field, value in InputValidation.fields(
            TestSuite, {key: value for key, value in fields.items() if value is not None}
        ).items():
            setattr(suite, field, value)
        if parent_id is not OptionalArgument.UNSET:
            suite.parent_id = parent_id
        suite.save()
        return {
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "parent_id": suite.parent_id,
        }
