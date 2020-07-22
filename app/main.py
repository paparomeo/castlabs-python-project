"""Starlette based proxy.

"""
import datetime
from typing import Any, Dict, List, Tuple
from urllib.parse import urlunsplit

import httpx
from starlette.responses import Response

from .config import JWT_DEFAULT_USERNAME
from .jwt import issue_jwt_for_user_and_date


async def app(scope: Dict[str, Any], receive: Any, send: Any) -> None:
    """HTTP proxy ASGI application.

    """
    assert scope["type"] == "http"
    method, url, headers, body = await arguments_from_downstream_request(scope, receive)
    updated_headers = add_jwt_header(headers)
    response = await upstream_request(method, url, updated_headers, body)
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


def add_jwt_header(headers: List[Tuple[bytes, bytes]]) -> List[Tuple[bytes, bytes]]:
    """Return a copy of headers with the addition of the x-my-jwt header.

    """
    user = (
        dict(headers)
        .get(b"username", JWT_DEFAULT_USERNAME.encode("utf-8"))
        .decode("utf-8")
    )
    jwt = issue_jwt_for_user_and_date(user, datetime.date.today())
    return [*headers, (b"x-my-jwt", jwt)]


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
