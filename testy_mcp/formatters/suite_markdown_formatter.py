from testy_mcp.services.input_validation import InputValidation


class SuiteMarkdownFormatter:
    def format(self, suite, suites, cases, steps_by_case) -> str:
        suites_by_id = {s.id: s for s in suites}
        cases_by_suite = {}
        for c in cases:
            cases_by_suite.setdefault(c.suite_id, []).append(c)
        lines = [f"# {suite.name}"]
        if suite.description:
            lines.append(f"\n{suite.description}\n")
        for case in cases_by_suite.get(suite.id, []):
            self._render_case_md(case, lines, steps_by_case)
        children = [s for s in suites if s.parent_id == suite.id]
        for child in sorted(children, key=lambda s: s.name):
            self._render_subtree_md(
                child, suites_by_id, cases_by_suite, lines, steps_by_case, level=2
            )
        return "\n".join(lines)

    def _render_subtree_md(self, suite, suites_by_id, cases_by_suite, lines, steps_by_case, level):
        prefix = "#" * level
        lines.append(f"\n{prefix} {suite.name}")
        if suite.description:
            lines.append(f"\n{suite.description}")
        for case in cases_by_suite.get(suite.id, []):
            self._render_case_md(case, lines, steps_by_case)
        children = [s for s in suites_by_id.values() if s.parent_id == suite.id]
        for child in sorted(children, key=lambda s: s.name):
            self._render_subtree_md(
                child, suites_by_id, cases_by_suite, lines, steps_by_case, min(level + 1, 6)
            )

    def _render_case_md(self, case, lines, steps_by_case):
        lines.append(f"\n### TC-{case.id}: {case.name}")
        if case.setup:
            lines.append(f"- **Preconditions:** {case.setup}")
        if case.scenario:
            lines.append(f"- **Steps:**\n{self._indent(case.scenario)}")
        if case.expected:
            lines.append(f"- **Expected result:** {case.expected}")
        if case.is_steps:
            for index, step in enumerate(steps_by_case.get(case.pk, []), start=1):
                lines.append(f"\n**Step {index}: {step.name}**")
                lines.append(f"- **Scenario:**\n{self._indent(step.scenario)}")
                if step.expected:
                    lines.append(f"- **Expected result:** {step.expected}")
        if case.teardown:
            lines.append(f"- **Postconditions:** {case.teardown}")
        if case.estimate:
            lines.append(f"- **Estimate:** {InputValidation.format_estimate(case.estimate)}")

    def _indent(self, text: str, prefix: str = "  ") -> str:
        return "\n".join((f"{prefix}{line}" for line in text.split("\n")))
