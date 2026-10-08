from testy.plugins.hooks import TestyPluginConfig
from testy.root.settings import common as _common_settings

from testy_mcp.oauth import OAuthMetadata


class TestyMcpConfig(TestyPluginConfig):
    package_name = "testy_mcp"
    verbose_name = "MCP Server"
    description = "Model Context Protocol server for AI integrations (Claude, Cursor)"
    version = "1.0.0"
    plugin_base_url = "mcp"
    urls_module = "testy_mcp.urls"
    author = "onitofu"
    middlewares = ["testy_mcp.middleware.OAuthWellKnownMiddleware"]

    @classmethod
    def configure(cls):
        origin_middleware = "testy_mcp.origin_middleware.McpOriginMiddleware"
        middlewares = _common_settings.MIDDLEWARE
        middlewares[:] = [
            middleware for middleware in middlewares if middleware != origin_middleware
        ]
        cors_middleware = "corsheaders.middleware.CorsMiddleware"
        origin_index = middlewares.index(cors_middleware) if cors_middleware in middlewares else 0
        middlewares.insert(origin_index, origin_middleware)
        if "oauth2_provider" not in _common_settings.INSTALLED_APPS:
            _common_settings.INSTALLED_APPS.append("oauth2_provider")
        if not hasattr(_common_settings, "OAUTH2_PROVIDER"):
            _common_settings.OAUTH2_PROVIDER = {}
        _common_settings.OAUTH2_PROVIDER["SCOPES"] = {
            scope: f"{scope} access" for scope in OAuthMetadata.SUPPORTED_SCOPES
        }
        _common_settings.OAUTH2_PROVIDER["DEFAULT_SCOPES"] = ["read", "write"]
        return cls
