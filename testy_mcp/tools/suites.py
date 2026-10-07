import logging

from django.db import transaction
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("testy_mcp")


def register(mcp: FastMCP):
    @mcp.tool()
    def list_suites(project_id: int, tree_view: bool = True, search: str = "") -> list[dict]:
        """List test suites in a project.

        Args:
            project_id: Project ID
            tree_view: Return as tree structure (default: True)
            search: Search by suite name
        """
        from testy.tests_description.models import TestSuite

        qs = TestSuite.objects.filter(project_id=project_id, is_deleted=False)
        if search:
            qs = qs.filter(name__icontains=search)

        suites = list(qs.values("id", "name", "description", "parent_id"))

        if not tree_view:
            return suites

        return _build_tree(suites)

    @mcp.tool()
    def create_suite(
        project_id: int, name: str, description: str = "", parent_id: int | None = None
    ) -> dict:
        """Create a test suite.

        Args:
            project_id: Project ID
            name: Suite name
            description: Suite description (supports Markdown)
            parent_id: Parent suite ID for nesting
        """
        from testy.tests_description.models import TestSuite

        suite = TestSuite.objects.create(
            project_id=project_id,
            name=name,
            description=description,
            parent_id=parent_id,
        )
        return {
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "parent_id": suite.parent_id,
        }

    @mcp.tool()
    def create_suites_bulk(project_id: int, suites: list[dict]) -> list[dict]:
        """Create multiple test suites in one atomic operation. Supports nested structure.

        Args:
            project_id: Project ID
            suites: Array of suites. Each suite:
                    {"name": str, "description": str, "children": [...]}
        """
        created = []
        with transaction.atomic():
            for suite_data in suites:
                created.extend(_create_suite_recursive(project_id, suite_data, parent_id=None))
        return created

    @mcp.tool()
    def update_suite(
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

    @mcp.tool()
    def delete_suite(suite_id: int) -> dict:
        """Delete a test suite (soft delete).

        Args:
            suite_id: Suite ID
        """
        from testy.tests_description.models import TestSuite

        suite = TestSuite.objects.get(id=suite_id, is_deleted=False)
        suite.is_deleted = True
        suite.save()
        return {"deleted": True, "id": suite_id}


def _create_suite_recursive(project_id: int, data: dict, parent_id: int | None) -> list[dict]:
    from testy.tests_description.models import TestSuite

    suite = TestSuite.objects.create(
        project_id=project_id,
        name=data["name"],
        description=data.get("description", ""),
        parent_id=parent_id,
    )
    result = [{"id": suite.id, "name": suite.name, "parent_id": suite.parent_id}]

    for child in data.get("children", []):
        result.extend(_create_suite_recursive(project_id, child, parent_id=suite.id))

    return result


def _build_tree(suites: list[dict]) -> list[dict]:
    by_id = {s["id"]: {**s, "children": []} for s in suites}
    roots = []
    for s in by_id.values():
        parent = s.get("parent_id")
        if parent and parent in by_id:
            by_id[parent]["children"].append(s)
        else:
            roots.append(s)
    return roots
