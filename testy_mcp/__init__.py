from testy.plugins.hooks import TestyPluginConfig, hookimpl
from testy.root.settings import common as _common_settings

from testy_mcp.oauth import SUPPORTED_SCOPES


class TestyMcpConfig(TestyPluginConfig):
    package_name = "testy_mcp"
    verbose_name = "MCP Server"
    description = "Model Context Protocol server for AI integrations (Claude, Cursor)"
    version = "1.0.0"
    plugin_base_url = "mcp"
    urls_module = "testy_mcp.urls"
    author = "arseniy.sotnikov@7bits.it"
    author_email = "arseniy.sotnikov@7bits.it"
    middlewares = ["testy_mcp.middleware.OAuthWellKnownMiddleware"]


@hookimpl
def config():
    if "oauth2_provider" not in _common_settings.INSTALLED_APPS:
        _common_settings.INSTALLED_APPS.append("oauth2_provider")
    if not hasattr(_common_settings, "OAUTH2_PROVIDER"):
        _common_settings.OAUTH2_PROVIDER = {}
    _common_settings.OAUTH2_PROVIDER["SCOPES"] = {
        scope: f"{scope} access" for scope in SUPPORTED_SCOPES
    }
    _common_settings.OAUTH2_PROVIDER["DEFAULT_SCOPES"] = ["read", "write"]
    return TestyMcpConfig
