from testy_mcp.context import RequestContext


class GetMeTool:
    name = "get_me"

    def execute(self) -> dict:
        """Get the username and name of the authenticated user."""
        user = RequestContext.get()
        if user is None:
            raise RuntimeError("Authenticated user is not available")
        return {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
