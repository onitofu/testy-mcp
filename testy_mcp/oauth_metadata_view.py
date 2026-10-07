from django.http import JsonResponse
from django.views import View

from testy_mcp.oauth import OAuthMetadata


class OAuthMetadataView(View):
    """OAuth 2.0 Authorization Server Metadata (RFC 8414).

    Returns metadata at .well-known/oauth-authorization-server so that
    MCP clients (Claude Code, Cursor) can auto-discover OAuth endpoints.
    """

    def get(self, request):
        return JsonResponse(OAuthMetadata.build(request))
