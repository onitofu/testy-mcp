from django.urls import path

from testy_mcp.oauth_metadata_view import OAuthMetadataView
from testy_mcp.transport import McpHttpView

urlpatterns = [
    path("", McpHttpView.as_view(), name="mcp-endpoint"),
    path(
        "oauth/.well-known/oauth-authorization-server",
        OAuthMetadataView.as_view(),
        name="oauth-metadata",
    ),
]
try:
    from oauth2_provider import views as oauth_views

    from testy_mcp.authorization_view import McpAuthorizationView

    urlpatterns += [
        path("oauth/authorize/", McpAuthorizationView.as_view(), name="oauth-authorize"),
        path("oauth/token/", oauth_views.TokenView.as_view(), name="oauth-token"),
        path("oauth/revoke/", oauth_views.RevokeTokenView.as_view(), name="oauth-revoke"),
    ]
except ImportError:
    pass
