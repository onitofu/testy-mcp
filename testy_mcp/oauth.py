class OAuthMetadata:
    SUPPORTED_SCOPES = ["openid", "email", "profile", "read", "write", "mcp:read", "mcp:write"]

    @classmethod
    def build(cls, request):
        """Build metadata shared by the root middleware and plugin view."""
        base_url = request.build_absolute_uri("/plugins/mcp")
        return {
            "issuer": request.build_absolute_uri("/"),
            "authorization_endpoint": f"{base_url}/oauth/authorize/",
            "token_endpoint": f"{base_url}/oauth/token/",
            "registration_endpoint": f"{base_url}/oauth/register/",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
            "scopes_supported": cls.SUPPORTED_SCOPES,
        }
