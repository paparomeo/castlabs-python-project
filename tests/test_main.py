# type: ignore
# pylint: disable=missing-module-docstring,disable=missing-function-docstring
import datetime
import json
import re
from http import HTTPStatus
from time import time

import pytest
from authlib.jose import jwt
from starlette.testclient import TestClient

from app.config import JWT_DEFAULT_USERNAME
from app.jwt import get_bytes_secret
from app.main import app, is_request_for_service

from .test_jwt import CLAIMS_OPTIONS

PROXY_HEADERS = {"host": "httpbin.org"}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.parametrize("username", [None, "foobar"])
def test_jwt_injection(username, client):
    headers = PROXY_HEADERS
    if username is not None:
        headers = {**PROXY_HEADERS, "username": "username"}
    response = client.post("/post", headers=headers, json={"foo": "bar"})
    assert response.ok
    token = response.json()["headers"]["X-My-Jwt"]
    claims = jwt.decode(token, get_bytes_secret(), claims_options=CLAIMS_OPTIONS)
    claims.validate()
    assert claims["iat"] < time()
    payload_claim = json.loads(claims["payload"])
    assert payload_claim["user"] == username or JWT_DEFAULT_USERNAME
    assert payload_claim["date"] <= datetime.date.today().isoformat()


def test_status(client):
    response = client.get("/status")
    assert response.ok
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    request_count = _get_request_count(response.text)
    seconds_since_startup = _get_seconds_since_startup(response.text)
    assert request_count >= 0
    assert seconds_since_startup > 0
    client.post("/post", headers=PROXY_HEADERS, json={"foo": "bar"})
    response = client.get("/status")
    assert _get_request_count(response.text) == request_count + 1
    assert _get_seconds_since_startup(response.text) > seconds_since_startup


def test_not_found(client):
    response = client.get("/foo")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_is_request_for_service():
    assert is_request_for_service(
        {"headers": [(b"host", b"localhost:8080")], "server": ("127.0.0.1", 8080)}
    )


def _get_request_count(html):
    return int(re.search(r"Proxied requests count: (\d+)", html).group(1))


def _get_seconds_since_startup(html):
    return float(re.search(r"Seconds since startup: (\d+\.\d+)", html).group(1))
