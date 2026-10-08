from django.apps import AppConfig


class TestyMcpAppConfig(AppConfig):
    name = "testy_mcp"

    def ready(self):
        from testy_mcp.services.oauth_token_revocation import OAuthTokenRevocation

        OAuthTokenRevocation.connect()
