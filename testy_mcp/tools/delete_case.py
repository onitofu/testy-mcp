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
        case = AccessControl().get("case", case_id, "destroy")
        case.is_deleted = True
        case.save()
        return {"deleted": True, "id": case_id}
