"""JWT module.

"""
import datetime
import json
from time import time
from uuid import uuid4

from authlib.jose import jwt

from .config import JWT_ALGORITHM, JWT_ISSUER, JWT_SHARED_SECRET


def get_bytes_secret(hex_encoded_secret: str = str(JWT_SHARED_SECRET)) -> bytes:
    """Get bytes for configured hexadecimal encoded secret.

    """
    return bytes.fromhex(hex_encoded_secret)


def issue_jwt_for_user_and_date(
    user: str,
    date: datetime.date,
    issuer: str = str(JWT_ISSUER),
    timestamp: int = int(time()),
    secret: bytes = get_bytes_secret(),
) -> bytes:
    """Issue JWT for given user and date.

    """
    header = {"alg": JWT_ALGORITHM}
    payload_claim = json.dumps({"user": user, "date": date.isoformat()})
    payload = {
        "iss": issuer,
        "iat": timestamp,
        "jti": uuid4().hex,
        "payload": payload_claim,
    }
    return bytes(jwt.encode(header, payload, secret))
