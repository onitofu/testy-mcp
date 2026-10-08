import base64
import inspect
import json
import logging

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import APIException, ValidationError

from testy_mcp.auth import RequestAuthenticator
from testy_mcp.json_rpc_error import JsonRpcError
from testy_mcp.oauth import OAuthMetadata

logger = logging.getLogger("testy_mcp")
MCP_PROTOCOL_VERSION = "2025-03-26"
SUPPORTED_MCP_PROTOCOL_VERSIONS = {"2025-06-18", "2025-03-26", "2024-11-05"}


@method_decorator(csrf_exempt, name="dispatch")
class McpHttpView(View):
    """MCP server endpoint using FastMCP public API (async).

    Routes JSON-RPC methods to FastMCP high-level methods.
    Uses async views since gunicorn runs with UvicornWorker.
    """

    async def post(self, request: HttpRequest) -> HttpResponse:
        try:
            user = await sync_to_async(RequestAuthenticator.authenticate)(request)
        except Exception:
            logger.exception("MCP authentication error")
            return self._error_response(-32603, "Internal error", None, status=500)
        if user is None:
            return JsonResponse(
                {"error": "Authentication required"},
                status=401,
                headers={"WWW-Authenticate": OAuthMetadata.authenticate_header(request)},
            )
        request.user = user
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return self._error_response(-32700, "Parse error", None)
        if not isinstance(body, dict):
            return self._error_response(-32600, "Invalid Request", None)
        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")
        is_notification = "id" not in body
        if not isinstance(method, str):
            return self._error_response(-32600, "Invalid Request", req_id)
        if not isinstance(params, dict):
            return self._error_response(-32602, "Invalid params", req_id)
        from simple_history.models import HistoricalRecords

        from testy_mcp.context import RequestContext
        from testy_mcp.server import mcp

        RequestContext.set(user)
        HistoricalRecords.context.request = request
        try:
            try:
                result = await self._dispatch(mcp, method, params)
                if is_notification:
                    return HttpResponse(status=202)
                return self._success_response(req_id, result)
            except JsonRpcError as exc:
                if is_notification:
                    return self._error_response(
                        exc.code, exc.message, None, status=400, data=exc.data
                    )
                return self._error_response(exc.code, exc.message, req_id, data=exc.data)
            except Exception:
                logger.exception("MCP request handling error for method: %s", method)
                if is_notification:
                    return self._error_response(-32603, "Internal error", None, status=500)
                return self._error_response(-32603, "Internal error", req_id)
        finally:
            RequestContext.set(None)
            try:
                del HistoricalRecords.context.request
            except AttributeError:
                pass

    async def _dispatch(self, mcp_server, method: str, params: dict):
        try:
            return await self._dispatch_method(mcp_server, method, params)
        except Exception as exc:
            error = self._expected_error(exc)
            if error is None:
                raise
            if method == "tools/call":
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": json.dumps(error, ensure_ascii=False)}],
                }
            raise JsonRpcError(-32000, "Request failed", data=error) from exc

    @staticmethod
    def _expected_error(exc):
        visited = set()
        while exc is not None and id(exc) not in visited:
            visited.add(id(exc))
            if isinstance(exc, APIException):
                return {"status_code": exc.status_code, "detail": exc.detail}
            if isinstance(exc, DjangoValidationError):
                return {
                    "status_code": 400,
                    "detail": exc.message_dict if hasattr(exc, "error_dict") else exc.messages,
                }
            if isinstance(exc, Http404):
                return {"status_code": 404, "detail": "Not found."}
            exc = exc.__cause__ or exc.__context__
        return None

    async def _dispatch_method(self, mcp_server, method: str, params: dict):
        """Route JSON-RPC method to the appropriate FastMCP handler."""
        if method == "initialize":
            requested_version = params.get("protocolVersion")
            protocol_version = (
                requested_version
                if requested_version in SUPPORTED_MCP_PROTOCOL_VERSIONS
                else MCP_PROTOCOL_VERSION
            )
            return {
                "protocolVersion": protocol_version,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False},
                },
                "serverInfo": {"name": mcp_server.name, "version": "1.0.0"},
            }
        if method == "tools/list":
            tools = await mcp_server.list_tools()
            return {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description or "",
                        "inputSchema": t.inputSchema
                        if isinstance(t.inputSchema, dict)
                        else t.inputSchema.model_dump()
                        if hasattr(t.inputSchema, "model_dump")
                        else {},
                    }
                    for t in tools
                ]
            }
        if method == "tools/call":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            if not isinstance(name, str) or not isinstance(arguments, dict):
                raise JsonRpcError(-32602, "Invalid tool call params")
            tool = mcp_server._tool_manager._tools.get(name)
            if tool is None:
                raise JsonRpcError(-32602, f"Unknown tool: {name}")
            try:
                inspect.signature(tool.fn).bind(**arguments)
            except TypeError as exc:
                raise ValidationError(str(exc)) from exc
            raw_result = await sync_to_async(tool.fn)(**arguments)
            if isinstance(raw_result, str):
                text = raw_result
            else:
                text = json.dumps(raw_result, ensure_ascii=False, default=str)
            return {"content": [{"type": "text", "text": text}]}
        if method == "resources/list":
            resources = await mcp_server.list_resources()
            return {
                "resources": [
                    {
                        "uri": str(r.uri),
                        "name": r.name or "",
                        "description": r.description or "",
                        "mimeType": r.mimeType or "text/plain",
                    }
                    for r in resources
                ]
            }
        if method == "resources/read":
            uri = params.get("uri", "")
            contents = await mcp_server.read_resource(uri)
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": c.mime_type
                        or (
                            "application/octet-stream"
                            if isinstance(c.content, bytes)
                            else "text/plain"
                        ),
                        **(
                            {"blob": base64.b64encode(c.content).decode("ascii")}
                            if isinstance(c.content, bytes)
                            else {"text": c.content}
                        ),
                    }
                    for c in contents
                ]
            }
        if method == "prompts/list":
            prompts = await mcp_server.list_prompts()
            return {
                "prompts": [
                    {
                        "name": p.name,
                        "description": p.description or "",
                        "arguments": [
                            {
                                "name": a.name,
                                "description": a.description or "",
                                "required": a.required,
                            }
                            for a in p.arguments or []
                        ],
                    }
                    for p in prompts
                ]
            }
        if method == "prompts/get":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = await mcp_server.get_prompt(name, arguments)
            return {
                "description": result.description or "",
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content.model_dump()
                        if hasattr(m.content, "model_dump")
                        else {"type": "text", "text": str(m.content)},
                    }
                    for m in result.messages
                ],
            }
        if method == "ping":
            return {}
        if method == "notifications/initialized":
            return None
        raise JsonRpcError(-32601, f"Method not found: {method}")

    def _success_response(self, req_id, result) -> JsonResponse:
        if result is None:
            return JsonResponse({"jsonrpc": "2.0", "result": {}, "id": req_id})
        return JsonResponse({"jsonrpc": "2.0", "result": result, "id": req_id})

    def _error_response(
        self, code: int, message: str, req_id, status: int | None = None, data=None
    ) -> JsonResponse:
        if status is None:
            status = 400 if code in {-32700, -32600, -32602} else 200
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return JsonResponse(
            {"jsonrpc": "2.0", "error": error, "id": req_id},
            status=status,
        )

    async def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(status=405)
