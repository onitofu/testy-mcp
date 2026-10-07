from django.db import transaction


class CreateSuitesBulkTool:
    name = "create_suites_bulk"

    def execute(self, project_id: int, suites: list[dict]) -> list[dict]:
        """Create multiple test suites in one atomic operation. Supports nested structure.

        Args:
            project_id: Project ID
            suites: Array of suites. Each suite:
                    {"name": str, "description": str, "children": [...]}
        """
        created = []
        with transaction.atomic():
            for suite_data in suites:
                created.extend(self._create_suite_recursive(project_id, suite_data, parent_id=None))
        return created

    def _create_suite_recursive(
        self, project_id: int, data: dict, parent_id: int | None
    ) -> list[dict]:
        from testy.tests_description.models import TestSuite

        suite = TestSuite.objects.create(
            project_id=project_id,
            name=data["name"],
            description=data.get("description", ""),
            parent_id=parent_id,
        )
        result = [{"id": suite.id, "name": suite.name, "parent_id": suite.parent_id}]
        for child in data.get("children", []):
            result.extend(self._create_suite_recursive(project_id, child, parent_id=suite.id))
        return result
