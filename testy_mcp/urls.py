from django.urls import path

from testy_mcp.transport import McpHttpView
from testy_mcp.oauth import OAuthMetadataView

urlpatterns = [
    # MCP Streamable HTTP endpoint (root of plugin)
    path('', McpHttpView.as_view(), name='mcp-endpoint'),

    # OAuth 2.0 endpoints
    path(
        'oauth/.well-known/oauth-authorization-server',
        OAuthMetadataView.as_view(),
        name='oauth-metadata',
    ),
]

# Conditionally add django-oauth-toolkit URLs
try:
    from oauth2_provider import views as oauth_views

    urlpatterns += [
        path('oauth/authorize/', oauth_views.AuthorizationView.as_view(), name='oauth-authorize'),
        path('oauth/token/', oauth_views.TokenView.as_view(), name='oauth-token'),
        path('oauth/revoke/', oauth_views.RevokeTokenView.as_view(), name='oauth-revoke'),
    ]

    # Dynamic Client Registration (RFC 7591) is handled by
    # OAuthWellKnownMiddleware._register_client()
except ImportError:
    pass
