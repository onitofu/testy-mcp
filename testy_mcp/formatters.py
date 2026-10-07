"""Formatters for exporting TestY data in LLM-friendly formats."""
import json


def format_suite_markdown(suite, suites, cases) -> str:
    suites_by_id = {s.id: s for s in suites}
    cases_by_suite = {}
    for c in cases:
        cases_by_suite.setdefault(c.suite_id, []).append(c)

    lines = [f'# {suite.name}']
    if suite.description:
        lines.append(f'\n{suite.description}\n')

    _render_suite_md(suite.id, suites_by_id, cases_by_suite, lines, level=2)

    # Render cases directly in root suite
    for case in cases_by_suite.get(suite.id, []):
        _render_case_md(case, lines)

    # Render child suites
    children = [s for s in suites if s.parent_id == suite.id]
    for child in sorted(children, key=lambda s: s.name):
        _render_subtree_md(child, suites_by_id, cases_by_suite, lines, level=2)

    return '\n'.join(lines)


def _render_subtree_md(suite, suites_by_id, cases_by_suite, lines, level):
    prefix = '#' * level
    lines.append(f'\n{prefix} {suite.name}')
    if suite.description:
        lines.append(f'\n{suite.description}')

    for case in cases_by_suite.get(suite.id, []):
        _render_case_md(case, lines)

    children = [s for s in suites_by_id.values() if s.parent_id == suite.id]
    for child in sorted(children, key=lambda s: s.name):
        _render_subtree_md(child, suites_by_id, cases_by_suite, lines, min(level + 1, 6))


def _render_suite_md(suite_id, suites_by_id, cases_by_suite, lines, level):
    pass  # Handled by _render_subtree_md


def _render_case_md(case, lines):
    lines.append(f'\n### TC-{case.id}: {case.name}')
    if case.setup:
        lines.append(f'- **Preconditions:** {case.setup}')
    if case.scenario:
        lines.append(f'- **Steps:**\n{_indent(case.scenario)}')
    if case.expected:
        lines.append(f'- **Expected result:** {case.expected}')
    if case.teardown:
        lines.append(f'- **Postconditions:** {case.teardown}')
    if case.estimate:
        lines.append(f'- **Estimate:** {case.estimate} min')


def _indent(text: str, prefix: str = '  ') -> str:
    return '\n'.join(f'{prefix}{line}' for line in text.split('\n'))


def format_suite_json(suite, suites, cases) -> str:
    suites_by_id = {s.id: s for s in suites}
    cases_by_suite = {}
    for c in cases:
        cases_by_suite.setdefault(c.suite_id, []).append(c)

    def build_node(s):
        node = {
            'id': s.id,
            'name': s.name,
            'cases': [_case_to_dict(c) for c in cases_by_suite.get(s.id, [])],
            'children': [],
        }
        children = [ch for ch in suites_by_id.values() if ch.parent_id == s.id]
        for child in sorted(children, key=lambda x: x.name):
            node['children'].append(build_node(child))
        return node

    return json.dumps({'suite': build_node(suite)}, ensure_ascii=False, indent=2)


def _case_to_dict(case) -> dict:
    return {
        'id': case.id,
        'name': case.name,
        'setup': case.setup,
        'scenario': case.scenario,
        'expected': case.expected,
        'teardown': case.teardown,
        'estimate': case.estimate,
    }


def format_plan_results_markdown(plan, test_results, stats, total) -> str:
    lines = [f'# Results: {plan.name}']
    if plan.started_at:
        period = f'{plan.started_at.strftime("%Y-%m-%d")}'
        if plan.due_date:
            period += f' — {plan.due_date.strftime("%Y-%m-%d")}'
        lines.append(f'\n**Period:** {period}')

    stats_str = ', '.join(f'{count} {name.lower()}' for name, count in sorted(stats.items()))
    lines.append(f'**Statistics:** {stats_str} (total: {total})')

    for test, result in test_results:
        status_name = test.last_status.name if test.last_status else 'Untested'
        lines.append(f'\n### TC-{test.case_id}: {test.case.name}')
        lines.append(f'- **Status:** {status_name}')
        if result:
            if result.comment:
                lines.append(f'- **Comment:** {result.comment}')
            if result.execution_time is not None:
                lines.append(f'- **Execution time:** {result.execution_time} sec')
            if result.user:
                lines.append(f'- **Executor:** {result.user.username}')
            lines.append(f'- **Date:** {result.created_at.strftime("%Y-%m-%d %H:%M:%S")}')

    return '\n'.join(lines)


def format_plan_results_json(plan, test_results, stats, total) -> str:
    data = {
        'plan': {
            'id': plan.id,
            'name': plan.name,
            'started_at': plan.started_at.isoformat() if plan.started_at else None,
            'due_date': plan.due_date.isoformat() if plan.due_date else None,
        },
        'statistics': stats,
        'total': total,
        'results': [],
    }

    for test, result in test_results:
        entry = {
            'test_id': test.id,
            'case_id': test.case_id,
            'case_name': test.case.name,
            'status': test.last_status.name if test.last_status else 'Untested',
        }
        if result:
            entry['comment'] = result.comment
            entry['execution_time'] = result.execution_time
            entry['executor'] = result.user.username if result.user else None
            entry['date'] = result.created_at.isoformat()
        data['results'].append(entry)

    return json.dumps(data, ensure_ascii=False, indent=2)
