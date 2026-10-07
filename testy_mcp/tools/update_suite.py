class UpdateSuiteTool:
    name = "update_suite"

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
        from testy.tests_description.models import TestSuite

        suite = TestSuite.objects.get(id=suite_id, is_deleted=False)
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
