class PlanResultsMarkdownFormatter:
    def format(self, plan, test_results, stats, total) -> str:
        lines = [f"# Results: {plan.name}"]
        if plan.started_at:
            period = f"{plan.started_at.strftime('%Y-%m-%d')}"
            if plan.due_date:
                period += f" — {plan.due_date.strftime('%Y-%m-%d')}"
            lines.append(f"\n**Period:** {period}")
        stats_str = ", ".join((f"{count} {name.lower()}" for name, count in sorted(stats.items())))
        lines.append(f"**Statistics:** {stats_str} (total: {total})")
        for test, result in test_results:
            status_name = test.last_status.name if test.last_status else "Untested"
            lines.append(f"\n### TC-{test.case_id}: {test.case.name}")
            lines.append(f"- **Status:** {status_name}")
            if result:
                if result.comment:
                    lines.append(f"- **Comment:** {result.comment}")
                if result.execution_time is not None:
                    lines.append(f"- **Execution time:** {result.execution_time} sec")
                if result.user:
                    lines.append(f"- **Executor:** {result.user.username}")
                lines.append(f"- **Date:** {result.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        return "\n".join(lines)
