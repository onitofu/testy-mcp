from testy_mcp.formatters.suite_json_formatter import SuiteJsonFormatter
from testy_mcp.formatters.suite_markdown_formatter import SuiteMarkdownFormatter
from testy_mcp.services.access_control import AccessControl


class ExportSuiteTool:
    name = "export_suite"

    def execute(
        self, suite_id: int, include_children: bool = True, format: str = "markdown"
    ) -> str:
        """Export all test cases with their steps; estimates use TestY duration strings.

        Args:
            suite_id: Suite ID
            include_children: Include nested suites (default: True)
            format: "markdown" (default) or "json"
        """
        access = AccessControl()
        suite = access.get("suite", suite_id)
        if include_children:
            all_suites = list(access.list("suite", suite.project_id))
            descendant_ids = self._get_descendant_ids(suite.id, all_suites)
            descendant_ids.add(suite.id)
        else:
            descendant_ids = {suite.id}
        suites = access.list("suite", suite.project_id).filter(id__in=descendant_ids)
        cases = (
            access.list("case", suite.project_id)
            .filter(suite_id__in=descendant_ids)
            .select_related("suite")
        )
        cases = list(cases)
        steps_by_case = {}
        for step in access.case_steps_many(cases):
            steps_by_case.setdefault(step.test_case_id, []).append(step)
        if format == "json":
            return SuiteJsonFormatter().format(suite, suites, cases, steps_by_case)
        return SuiteMarkdownFormatter().format(suite, suites, cases, steps_by_case)

    def _get_descendant_ids(self, suite_id: int, all_suites) -> set:
        children_map = {}
        for s in all_suites:
            pid = s.parent_id
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(s.id)
        result = set()
        stack = children_map.get(suite_id, [])
        while stack:
            sid = stack.pop()
            result.add(sid)
            stack.extend(children_map.get(sid, []))
        return result
