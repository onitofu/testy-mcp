import json
import secrets

from django.http import JsonResponse
from testy_mcp.oauth import SUPPORTED_SCOPES


class OAuthWellKnownMiddleware:
    """Serve OAuth metadata and handle Dynamic Client Registration.

    MCP clients (Claude Code, Cursor) need:
    1. OAuth metadata at /.well-known/oauth-authorization-server (root level)
    2. Dynamic Client Registration (RFC 7591) at /plugins/mcp/oauth/register/
    """

    WELL_KNOWN_PATH = '/.well-known/oauth-authorization-server'
    REGISTER_PATH = '/plugins/mcp/oauth/register/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == self.WELL_KNOWN_PATH:
            return self._oauth_metadata(request)
        if request.path == self.REGISTER_PATH and request.method == 'POST':
            return self._register_client(request)
        return self.get_response(request)

    def _oauth_metadata(self, request):
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

    def _register_client(self, request):
        """Dynamic Client Registration (RFC 7591)."""
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'invalid_client_metadata'}, status=400)

        from oauth2_provider.models import Application

        client_name = body.get('client_name', 'MCP Client')
        redirect_uris = body.get('redirect_uris', [])
        grant_types = body.get('grant_types', ['authorization_code'])
        token_endpoint_auth_method = body.get('token_endpoint_auth_method', 'none')

        # Determine client type based on auth method
        if token_endpoint_auth_method == 'none':
            client_type = Application.CLIENT_PUBLIC
            client_secret = ''
        else:
            client_type = Application.CLIENT_CONFIDENTIAL
            client_secret = secrets.token_urlsafe(48)

        app = Application.objects.create(
            name=client_name,
            client_type=client_type,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=' '.join(redirect_uris) if isinstance(redirect_uris, list) else redirect_uris,
            client_secret=client_secret,
            skip_authorization=True,
        )

        response_data = {
            'client_id': app.client_id,
            'client_name': client_name,
            'redirect_uris': redirect_uris,
            'grant_types': grant_types,
            'token_endpoint_auth_method': token_endpoint_auth_method,
        }
        if client_secret:
            response_data['client_secret'] = client_secret

        return JsonResponse(response_data, status=201)
