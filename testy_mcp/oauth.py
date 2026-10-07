class OAuthMetadata:
    SUPPORTED_SCOPES = ["openid", "email", "profile", "read", "write", "mcp:read", "mcp:write"]
    RESOURCE_PATH = "/plugins/mcp/"
    PROTECTED_RESOURCE_METADATA_PATH = f"/.well-known/oauth-protected-resource{RESOURCE_PATH}"

    @classmethod
    def resource_url(cls, request):
        return request.build_absolute_uri(cls.RESOURCE_PATH)

    @classmethod
    def protected_resource_metadata_url(cls, request):
        return request.build_absolute_uri(cls.PROTECTED_RESOURCE_METADATA_PATH)

    @classmethod
    def issuer_url(cls, request):
        return request.build_absolute_uri("/")

    @classmethod
    def build_protected_resource(cls, request):
        return {
            "resource": cls.resource_url(request),
            "authorization_servers": [cls.issuer_url(request)],
            "scopes_supported": cls.SUPPORTED_SCOPES,
            "bearer_methods_supported": ["header"],
        }

    @classmethod
    def authenticate_header(cls, request):
        return f'Bearer resource_metadata="{cls.protected_resource_metadata_url(request)}"'

    @classmethod
    def build(cls, request):
        """Build metadata shared by the root middleware and plugin view."""
        base_url = cls.resource_url(request).rstrip("/")
        return {
            "issuer": cls.issuer_url(request),
            "authorization_endpoint": f"{base_url}/oauth/authorize/",
            "token_endpoint": f"{base_url}/oauth/token/",
            "registration_endpoint": f"{base_url}/oauth/register/",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
            "scopes_supported": cls.SUPPORTED_SCOPES,
        }
