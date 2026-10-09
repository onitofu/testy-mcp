from copy import copy
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from jsonschema import Draft202012Validator

from testy_mcp.oauth import OAuthMetadata


class OAuthClientRegistration:
    """Validate dynamic client metadata before persisting an OAuth application."""

    @staticmethod
    def validate(body):
        schema = {
            "type": "object",
            "required": ["redirect_uris"],
            "properties": {
                "client_name": {"type": "string"},
                "redirect_uris": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string"},
                },
                "grant_types": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"enum": OAuthMetadata.SUPPORTED_GRANT_TYPES},
                    "contains": {"const": "authorization_code"},
                },
                "token_endpoint_auth_method": {"enum": OAuthMetadata.SUPPORTED_TOKEN_AUTH_METHODS},
            },
        }
        if not Draft202012Validator(schema).is_valid(body):
            raise ValidationError("Invalid client metadata.", code="invalid_client_metadata")
        return {
            "client_name": body.get("client_name", "MCP Client"),
            "redirect_uris": body["redirect_uris"],
            "grant_types": OAuthMetadata.SUPPORTED_GRANT_TYPES.copy(),
            "token_endpoint_auth_method": body.get("token_endpoint_auth_method", "none"),
        }

    @staticmethod
    def validate_redirect_uris(redirect_uris, application):
        for uri in redirect_uris:
            try:
                if any(character.isspace() for character in uri):
                    raise ValueError("Whitespace in redirect URI.")
                urlsplit(uri).port
                candidate = copy(application)
                candidate.redirect_uris = uri
                candidate.clean()
            except (ValidationError, ValueError) as exc:
                raise ValidationError("Invalid redirect URI.", code="invalid_redirect_uri") from exc
