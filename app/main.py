"""Starlette based proxy.

"""
from typing import Any, Dict, List, Tuple
from urllib.parse import urlunsplit

import httpx
from starlette.responses import Response


async def app(scope: Dict[str, Any], receive: Any, send: Any) -> None:
    """HTTP proxy ASGI application.

    """
    assert scope["type"] == "http"
    method, url, headers, body = await arguments_from_downstream_request(scope, receive)
    response = await upstream_request(method, url, headers, body)
    await response(scope, receive, send)


async def arguments_from_downstream_request(
    scope: Dict[str, Any], receive: Any
) -> Tuple[str, str, List[Tuple[bytes, bytes]], bytes]:
    """Extract arguments required for upstream request from downstream request.

    """
    body = bytearray()
    more_body = True
    while more_body:
        message = await receive()
        assert message["type"] == "http.request"
        body.extend(message.get("body", b""))
        more_body = message.get("more_body", False)
    method = scope["method"]
    url = upstream_url_from_scope(scope)
    headers = scope["headers"]
    return method, url, headers, bytes(body)


def upstream_url_from_scope(scope: Dict[str, Any]) -> str:
    """Build upstream url from ASGI scope.

    """
    host = dict(scope["headers"])[b"host"]
    return urlunsplit(
        (
            scope["scheme"].encode("utf-8"),
            host,
            scope["path"].encode("utf-8"),
            scope["query_string"],
            b"",
        )
    ).decode("utf-8")


async def upstream_request(
    method: str, url: str, headers: List[Tuple[bytes, bytes]], body: bytes
) -> Response:
    """Make upstream request and build a suitable proxy response.

    """
    response_body = bytearray()
    client = httpx.AsyncClient()
    async with client.stream(
        method, url, headers=headers, data=body
    ) as upstream_response:
        async for chunk in upstream_response.aiter_raw():
            response_body.extend(chunk)
    response_kwargs = {
        name: getattr(upstream_response, name) for name in ["status_code", "headers"]
    }
    return Response(bytes(response_body), **response_kwargs)