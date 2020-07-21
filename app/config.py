"""Application configuration module.

"""
from pathlib import Path

from starlette.config import Config
from starlette.datastructures import URL, Secret

_config_pathname = Path(__file__).parent.parent / ".env"
_config = Config(_config_pathname)

JWT_ALGORITHM = _config("JWT_ALGORITHM", default="HS512")
JWT_ISSUER = _config("JWT_ISSUER", cast=URL, default="https://castlabs.com")
JWT_SHARED_SECRET = _config("JWT_SHARED_SECRET", cast=Secret)
