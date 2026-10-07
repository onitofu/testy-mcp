from testy_mcp.formatters.suite_json_formatter import SuiteJsonFormatter
from testy_mcp.formatters.suite_markdown_formatter import SuiteMarkdownFormatter


class ExportSuiteTool:
    name = "export_suite"

    def execute(
        self, suite_id: int, include_children: bool = True, format: str = "markdown"
    ) -> str:
        """Export all test cases in a suite in LLM-friendly format.

        Args:
            suite_id: Suite ID
            include_children: Include nested suites (default: True)
            format: "markdown" (default) or "json"
        """
        from testy.tests_description.models import TestCase, TestSuite

        suite = TestSuite.objects.get(id=suite_id, is_deleted=False)
        if include_children:
            all_suites = list(TestSuite.objects.filter(project=suite.project, is_deleted=False))
            descendant_ids = self._get_descendant_ids(suite.id, all_suites)
            descendant_ids.add(suite.id)
        else:
            descendant_ids = {suite.id}
        suites = TestSuite.objects.filter(id__in=descendant_ids, is_deleted=False)
        cases = TestCase.objects.filter(
            suite_id__in=descendant_ids, is_deleted=False
        ).select_related("suite")
        if format == "json":
            return SuiteJsonFormatter().format(suite, suites, cases)
        return SuiteMarkdownFormatter().format(suite, suites, cases)

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
