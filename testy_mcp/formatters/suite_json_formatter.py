import json


class SuiteJsonFormatter:
    def format(self, suite, suites, cases) -> str:
        suites_by_id = {s.id: s for s in suites}
        cases_by_suite = {}
        for c in cases:
            cases_by_suite.setdefault(c.suite_id, []).append(c)

        def build_node(s):
            node = {
                "id": s.id,
                "name": s.name,
                "cases": [self._case_to_dict(c) for c in cases_by_suite.get(s.id, [])],
                "children": [],
            }
            children = [ch for ch in suites_by_id.values() if ch.parent_id == s.id]
            for child in sorted(children, key=lambda x: x.name):
                node["children"].append(build_node(child))
            return node

        return json.dumps({"suite": build_node(suite)}, ensure_ascii=False, indent=2)

    def _case_to_dict(self, case) -> dict:
        return {
            "id": case.id,
            "name": case.name,
            "setup": case.setup,
            "scenario": case.scenario,
            "expected": case.expected,
            "teardown": case.teardown,
            "estimate": case.estimate,
        }
