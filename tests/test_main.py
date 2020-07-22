# type: ignore
# pylint: disable=missing-module-docstring,disable=missing-function-docstring
import datetime
import json
from time import time

import pytest
from authlib.jose import jwt
from starlette.testclient import TestClient

from app.config import JWT_DEFAULT_USERNAME
from app.jwt import get_bytes_secret
from app.main import app

from .test_jwt import CLAIMS_OPTIONS


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.parametrize("username", [None, "foobar"])
def test_jwt_injection(username, client):
    headers = {"host": "httpbin.org"}
    if username is not None:
        headers["username"] = username
    response = client.post("/post", headers=headers, json={"foo": "bar"})
    assert response.ok
    token = response.json()["headers"]["X-My-Jwt"]
    claims = jwt.decode(token, get_bytes_secret(), claims_options=CLAIMS_OPTIONS)
    claims.validate()
    assert claims["iat"] < time()
    payload_claim = json.loads(claims["payload"])
    assert payload_claim["user"] == username or JWT_DEFAULT_USERNAME
    assert payload_claim["date"] <= datetime.date.today().isoformat()
