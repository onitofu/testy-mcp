"""OAuth 2.0 configuration for MCP server.

Uses django-oauth-toolkit to provide OAuth 2.0 Authorization Code + PKCE flow.
Supports Dynamic Client Registration (RFC 7591) for seamless AI client setup.
"""
from django.http import JsonResponse
from django.views import View

SUPPORTED_SCOPES = ['openid', 'email', 'profile', 'read', 'write', 'mcp:read', 'mcp:write']


class OAuthMetadataView(View):
    """OAuth 2.0 Authorization Server Metadata (RFC 8414).

    Returns metadata at .well-known/oauth-authorization-server so that
    MCP clients (Claude Code, Cursor) can auto-discover OAuth endpoints.
    """

    def get(self, request):
        base_url = request.build_absolute_uri('/plugins/mcp')
        issuer = request.build_absolute_uri('/')

        return JsonResponse({
            'issuer': issuer,
            'authorization_endpoint': f'{base_url}/oauth/authorize/',
            'token_endpoint': f'{base_url}/oauth/token/',
            'registration_endpoint': f'{base_url}/oauth/register/',
            'response_types_supported': ['code'],
            'grant_types_supported': ['authorization_code', 'refresh_token'],
            'code_challenge_methods_supported': ['S256'],
            'token_endpoint_auth_methods_supported': ['client_secret_post', 'none'],
            'scopes_supported': SUPPORTED_SCOPES,
        })
