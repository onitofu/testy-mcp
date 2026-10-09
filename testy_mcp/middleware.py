import json
import secrets

from django.core.exceptions import ValidationError
from django.http import JsonResponse

from testy_mcp.oauth import OAuthMetadata
from testy_mcp.services.oauth_client_registration import OAuthClientRegistration


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
        from oauth2_provider.models import get_application_model

        try:
            metadata = OAuthClientRegistration.validate(body)
            Application = get_application_model()
            if metadata["token_endpoint_auth_method"] == "none":
                client_type = Application.CLIENT_PUBLIC
                client_secret = ""
            else:
                client_type = Application.CLIENT_CONFIDENTIAL
                client_secret = secrets.token_urlsafe(48)
            app = Application(
                name=metadata["client_name"],
                client_type=client_type,
                authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
                redirect_uris=" ".join(metadata["redirect_uris"]),
                client_secret=client_secret,
                skip_authorization=False,
            )
            OAuthClientRegistration.validate_redirect_uris(metadata["redirect_uris"], app)
            app.full_clean()
        except ValidationError as exc:
            return JsonResponse(
                {"error": getattr(exc, "code", "invalid_client_metadata")}, status=400
            )
        app.save()
        response_data = {"client_id": app.client_id, **metadata}
        if client_secret:
            response_data["client_secret"] = client_secret
        return JsonResponse(response_data, status=201)
