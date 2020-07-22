"""Starlette based proxy.

"""
import datetime
import socket
import time
from http import HTTPStatus
from typing import Any, Dict, List, Tuple
from urllib.parse import urlunsplit

import httpx
from starlette.responses import HTMLResponse, PlainTextResponse, Response

from .config import JWT_DEFAULT_USERNAME
from .jwt import issue_jwt_for_user_and_date


class Status:  # pylint: disable=too-few-public-methods
    """Proxy status.

    """

    startup_time: float = time.time()
    proxied_requests_count: int = 0


async def app(scope: Dict[str, Any], receive: Any, send: Any) -> None:
    """HTTP proxy ASGI application.

    """
    assert scope["type"] in ["lifespan", "http"]
    if scope["type"] == "lifespan":  # pragma: no cover
        await send(lifespan_event_handler())
        return
    if is_request_for_service(scope):
        response = service_handler(scope)
    else:
        method, url, headers, body = await arguments_from_downstream_request(
            scope, receive
        )
        updated_headers = add_jwt_header(headers)
        response = await upstream_request(method, url, updated_headers, body)
        Status.proxied_requests_count += 1
    await response(scope, receive, send)


def lifespan_event_handler() -> Dict[str, str]:  # pragma: no cover
    """Handle lifespan event and return response for ASGI server.

    """
    Status.startup_time = time.time()
    Status.proxied_requests_count = 0
    return {"type": "lifespan.startup.complete"}


def is_request_for_service(scope: Dict[str, Any]) -> bool:
    """Is this a direct request for the service or meant to proxied?

    """
    host = get_host(scope).decode("utf-8")
    port = "80"
    if ":" in host:
        host, port = host.split(":")
    try:
        addrinfo = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return True
    return scope["server"] in [info[4] for info in addrinfo]


def get_host(scope: Dict[str, Any]) -> bytes:
    """Extract the request host from the scope's headers.

    """
    return bytes(dict(scope["headers"])[b"host"])


def service_handler(scope: Dict[str, Any]) -> Response:
    """Handle requests directly for the service.

    """
    if scope["path"] == "/status":
        elapsed_time = round(time.time() - Status.startup_time, 3)
        return HTMLResponse(
            f"""
<html>
  <body>
    <h1>Seconds since startup: {elapsed_time}</h1>
    <h1>Proxied requests count: {Status.proxied_requests_count}</h1>
  </body>
</html>
""".strip()
        )
    return PlainTextResponse(
        HTTPStatus.NOT_FOUND.phrase, status_code=HTTPStatus.NOT_FOUND
    )


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
