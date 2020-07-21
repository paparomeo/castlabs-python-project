# type: ignore
# pylint: disable=missing-module-docstring,missing-class-docstring
# pylint: disable=missing-function-docstring
import datetime
import json
from time import time

from authlib.jose import jwt

from app.config import JWT_ISSUER
from app.jwt import get_bytes_secret, issue_jwt_for_user_and_date

CLAIMS_OPTIONS = {
    "iss": {"essential": True, "values": [JWT_ISSUER]},
    "iat": {"essential": True},
    "jti": {"essential": True},
    "payload": {"essential": True},
}


def test_issue_jwt_for_user():
    today = datetime.date.today()
    token = issue_jwt_for_user_and_date("foo", today)
    claims = jwt.decode(token, get_bytes_secret(), claims_options=CLAIMS_OPTIONS)
    claims.validate()
    assert claims["iat"] < time()
    assert json.loads(claims["payload"]) == {"user": "foo", "date": today.isoformat()}
