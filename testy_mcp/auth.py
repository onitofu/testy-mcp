from django.http import HttpRequest


class RequestAuthenticator:
    @classmethod
    def authenticate(cls, request: HttpRequest):
        """Extract authenticated user from request.

        Supports:
        1. OAuth 2.0 Bearer token (django-oauth-toolkit)
        2. TestY TTL token (Authorization: Token <key>)
        3. Django session authentication
        """
        request.mcp_scopes = None
        user = cls._authenticate_oauth(request)
        if user:
            return user
        user = cls._authenticate_ttl_token(request)
        if user:
            return user
        if hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None

    @classmethod
    def _authenticate_oauth(cls, request: HttpRequest):
        """Authenticate via OAuth 2.0 Bearer token."""
        from oauth2_provider.contrib.rest_framework import OAuth2Authentication

        auth = OAuth2Authentication()
        result = auth.authenticate(request)
        if result:
            request.mcp_scopes = frozenset(result[1].scope.split())
            return result[0]
        return None

    @classmethod
    def _authenticate_ttl_token(cls, request: HttpRequest):
        """Authenticate via TestY TTL token."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Token "):
            return None
        token_key = auth_header[6:].strip()
        from django.utils import timezone
        from testy.root.auth.models import TTLToken

        try:
            token = TTLToken.objects.select_related("user").get(key=token_key)
        except TTLToken.DoesNotExist:
            return None
        if not token.user.is_active:
            return None
        if token.expiration_date and token.expiration_date <= timezone.now():
            return None
        return token.user
