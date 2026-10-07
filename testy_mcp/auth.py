import logging

from django.http import HttpRequest

logger = logging.getLogger('testy_mcp')


def get_user_from_request(request: HttpRequest):
    """Extract authenticated user from request.

    Supports:
    1. OAuth 2.0 Bearer token (django-oauth-toolkit)
    2. TestY TTL token (Authorization: Token <key>)
    3. Django session authentication
    """
    # 1. OAuth 2.0 Bearer token
    user = _authenticate_oauth(request)
    if user:
        return user

    # 2. TTL Token
    user = _authenticate_ttl_token(request)
    if user:
        return user

    # 3. Session
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user

    return None


def _authenticate_oauth(request: HttpRequest):
    """Authenticate via OAuth 2.0 Bearer token."""
    try:
        from oauth2_provider.contrib.rest_framework import OAuth2Authentication
        auth = OAuth2Authentication()
        result = auth.authenticate(request)
        if result:
            return result[0]
    except (ImportError, Exception):
        pass
    return None


def _authenticate_ttl_token(request: HttpRequest):
    """Authenticate via TestY TTL token."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Token '):
        return None

    token_key = auth_header[6:].strip()
    try:
        from root.auth.models import TTLToken
        token = TTLToken.objects.select_related('user').get(key=token_key)

        from django.utils import timezone
        if token.expiration_date and token.expiration_date < timezone.now():
            return None

        return token.user
    except Exception:
        return None
