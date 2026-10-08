from django.db import transaction

from testy_mcp.services.access_control import AccessControl


class DeleteCaseTool:
    name = "delete_case"

    @transaction.atomic
    def execute(self, case_id: int) -> dict:
        """Delete a test case (soft delete).

        Args:
            case_id: Test case ID
        """
        AccessControl().delete("case", case_id)
        return {"deleted": True, "id": case_id}
