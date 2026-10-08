from urllib.parse import urlsplit

from django.http import JsonResponse
from django.http.request import split_domain_port
from django.middleware.csrf import CsrfViewMiddleware

from testy_mcp.oauth import OAuthMetadata


class McpOriginMiddleware:
    """Validate MCP origins independently of authentication and CORS."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.csrf_check = CsrfViewMiddleware(get_response)

    def __call__(self, request):
        if (
            request.path_info.rstrip("/") == OAuthMetadata.RESOURCE_PATH.rstrip("/")
            and "HTTP_ORIGIN" in request.META
            and not self._origin_allowed(request)
        ):
            return JsonResponse({"error": "Origin not allowed"}, status=403)
        return self.get_response(request)

    def _origin_allowed(self, request):
        origin = request.META["HTTP_ORIGIN"]
        try:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or not split_domain_port(parsed.netloc)[0]
                or parsed.username is not None
                or parsed.password is not None
                or origin != f"{parsed.scheme}://{parsed.netloc}"
            ):
                return False
            parsed.port
        except ValueError:
            return False
        return self.csrf_check._origin_verified(request)
