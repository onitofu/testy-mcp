class SuiteMarkdownFormatter:
    def format(self, suite, suites, cases) -> str:
        suites_by_id = {s.id: s for s in suites}
        cases_by_suite = {}
        for c in cases:
            cases_by_suite.setdefault(c.suite_id, []).append(c)
        lines = [f"# {suite.name}"]
        if suite.description:
            lines.append(f"\n{suite.description}\n")
        for case in cases_by_suite.get(suite.id, []):
            self._render_case_md(case, lines)
        children = [s for s in suites if s.parent_id == suite.id]
        for child in sorted(children, key=lambda s: s.name):
            self._render_subtree_md(child, suites_by_id, cases_by_suite, lines, level=2)
        return "\n".join(lines)

    def _render_subtree_md(self, suite, suites_by_id, cases_by_suite, lines, level):
        prefix = "#" * level
        lines.append(f"\n{prefix} {suite.name}")
        if suite.description:
            lines.append(f"\n{suite.description}")
        for case in cases_by_suite.get(suite.id, []):
            self._render_case_md(case, lines)
        children = [s for s in suites_by_id.values() if s.parent_id == suite.id]
        for child in sorted(children, key=lambda s: s.name):
            self._render_subtree_md(child, suites_by_id, cases_by_suite, lines, min(level + 1, 6))

    def _render_case_md(self, case, lines):
        lines.append(f"\n### TC-{case.id}: {case.name}")
        if case.setup:
            lines.append(f"- **Preconditions:** {case.setup}")
        if case.scenario:
            lines.append(f"- **Steps:**\n{self._indent(case.scenario)}")
        if case.expected:
            lines.append(f"- **Expected result:** {case.expected}")
        if case.teardown:
            lines.append(f"- **Postconditions:** {case.teardown}")
        if case.estimate:
            lines.append(f"- **Estimate:** {case.estimate} min")

    def _indent(self, text: str, prefix: str = "  ") -> str:
        return "\n".join((f"{prefix}{line}" for line in text.split("\n")))
