from django.db import transaction

from testy_mcp.services.access_control import AccessControl


class DeleteSuiteTool:
    name = "delete_suite"

    @transaction.atomic
    def execute(self, suite_id: int) -> dict:
        """Delete a test suite (soft delete).

        Args:
            suite_id: Suite ID
        """
        suite = AccessControl().get("suite", suite_id, "destroy")
        suite.is_deleted = True
        suite.save()
        return {"deleted": True, "id": suite_id}
