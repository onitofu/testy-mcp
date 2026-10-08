from testy_mcp.services.access_control import AccessControl


class ProjectStatusesResource:
    name = "project_statuses"
    uri = "testy://project/{project_id}/statuses"

    def execute(self, project_id: int) -> str:
        """List of available result statuses."""
        statuses = AccessControl().list("status", project_id)
        lines = ["Available result statuses:", ""]
        for s in statuses:
            stype = "system" if s.type == 0 else "custom"
            lines.append(f"- {s.name} ({stype}, color: {s.color})")
        return "\n".join(lines)
