from pathlib import Path
import os
import socket

from src.common.logger_setup import logger

CONFIGURATION_TYPE = os.getenv("CONFIGURATION_TYPE", None)
if CONFIGURATION_TYPE is None:
    raise RuntimeError(
        "CONFIGURATION_TYPE was not set! Must be local, dev, prod. Aborting."
    )

IS_PROD = CONFIGURATION_TYPE == "prod"
IS_DEV = CONFIGURATION_TYPE == "dev"
IS_LOCAL = CONFIGURATION_TYPE == "local"

if IS_LOCAL:
    G_CLIENT_ID = (
        "1084736521175-4p43u0ddhru6qs6aqd6n4r2smmnffqcu.apps.googleusercontent.com"
    )
    CORS_ORIGIN = "*"
    MIN_VALID_PROXY_PORT = 26600
    MAX_VALID_PROXY_PORT = 26700
    API_HOST = "api.localhost"
    HOSTNAME = "localhost"
elif IS_DEV:
    G_CLIENT_ID = (
        "1084736521175-2b5rrrpcs422qdc5458dhisdsj8auo0p.apps.googleusercontent.com"
    )
    CORS_ORIGIN = "https://dev.yakumo.yukkuricraft.net"
    MIN_VALID_PROXY_PORT = 26600
    MAX_VALID_PROXY_PORT = 26700
    API_HOST = "dev.api.yukkuricraft.net"
    HOSTNAME = "yukkuricraft.net"
elif IS_PROD:
    G_CLIENT_ID = (
        "1084736521175-2b5rrrpcs422qdc5458dhisdsj8auo0p.apps.googleusercontent.com"
    )
    CORS_ORIGIN = "https://yakumo.yukkuricraft.net"
    MIN_VALID_PROXY_PORT = 25600
    MAX_VALID_PROXY_PORT = 25700
    API_HOST = "api.yukkuricraft.net"
    HOSTNAME = "yukkuricraft.net"
else:
    raise RuntimeError(f"Found running on an unknown environment! CONFIGURATION_TYPE was '${CONFIGURATION_TYPE}'")

HOST_PASSWD = "/etc/host-passwd"
WHITELISTED_USERS_FILE = "secrets/whitelisted_google_sub_ids.txt"
ACCESS_TOKEN_DUR_MINS = 30
YC_TOKEN_AUTH_SCHEME = "YC-Token"
ENV_FOLDER: Path = Path("/app/env")
