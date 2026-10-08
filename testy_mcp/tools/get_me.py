from testy_mcp.services.access_control import AccessControl


class GetMeTool:
    name = "get_me"

    def execute(self) -> dict:
        """Get the username and name of the authenticated user."""
        access = AccessControl()
        access.require_scope("retrieve")
        user = access.user
        return {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
