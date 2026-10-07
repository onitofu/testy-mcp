from testy.plugins.hooks import hookimpl

from testy_mcp.testy_mcp_config import TestyMcpConfig


@hookimpl
def config():
    return TestyMcpConfig.configure()
