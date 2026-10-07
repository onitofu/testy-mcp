class DeleteSuiteTool:
    name = "delete_suite"

    def execute(self, suite_id: int) -> dict:
        """Delete a test suite (soft delete).

        Args:
            suite_id: Suite ID
        """
        from testy.tests_description.models import TestSuite

        suite = TestSuite.objects.get(id=suite_id, is_deleted=False)
        suite.is_deleted = True
        suite.save()
        return {"deleted": True, "id": suite_id}
