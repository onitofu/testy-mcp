class DeleteCaseTool:
    name = "delete_case"

    def execute(self, case_id: int) -> dict:
        """Delete a test case (soft delete).

        Args:
            case_id: Test case ID
        """
        from testy.tests_description.models import TestCase

        case = TestCase.objects.get(id=case_id, is_deleted=False)
        case.is_deleted = True
        case.save()
        return {"deleted": True, "id": case_id}
