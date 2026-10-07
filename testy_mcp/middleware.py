import json
import secrets

from django.http import JsonResponse

from testy_mcp.oauth import OAuthMetadata


class OAuthWellKnownMiddleware:
    """Serve OAuth discovery metadata and handle Dynamic Client Registration."""

    WELL_KNOWN_PATH = "/.well-known/oauth-authorization-server"
    REGISTER_PATH = "/plugins/mcp/oauth/register/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == OAuthMetadata.PROTECTED_RESOURCE_METADATA_PATH:
            if request.method != "GET":
                return JsonResponse(
                    {"error": "Method not allowed"}, status=405, headers={"Allow": "GET"}
                )
            return JsonResponse(OAuthMetadata.build_protected_resource(request))
        if request.path == self.WELL_KNOWN_PATH:
            return self._oauth_metadata(request)
        if request.path == self.REGISTER_PATH and request.method == "POST":
            return self._register_client(request)
        return self.get_response(request)

    def _oauth_metadata(self, request):
        return JsonResponse(OAuthMetadata.build(request))

    def _register_client(self, request):
        """Dynamic Client Registration (RFC 7591)."""
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid_client_metadata"}, status=400)
        from oauth2_provider.models import Application

        client_name = body.get("client_name", "MCP Client")
        redirect_uris = body.get("redirect_uris", [])
        grant_types = body.get("grant_types", ["authorization_code"])
        token_endpoint_auth_method = body.get("token_endpoint_auth_method", "none")
        if token_endpoint_auth_method == "none":
            client_type = Application.CLIENT_PUBLIC
            client_secret = ""
        else:
            client_type = Application.CLIENT_CONFIDENTIAL
            client_secret = secrets.token_urlsafe(48)
        app = Application.objects.create(
            name=client_name,
            client_type=client_type,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=" ".join(redirect_uris)
            if isinstance(redirect_uris, list)
            else redirect_uris,
            client_secret=client_secret,
            skip_authorization=True,
        )
        response_data = {
            "client_id": app.client_id,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
            "grant_types": grant_types,
            "token_endpoint_auth_method": token_endpoint_auth_method,
        }
        if client_secret:
            response_data["client_secret"] = client_secret
        return JsonResponse(response_data, status=201)
