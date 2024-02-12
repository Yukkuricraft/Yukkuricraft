from pathlib import Path
import socket

G_CLIENT_ID = (
    "1084736521175-2b5rrrpcs422qdc5458dhisdsj8auo0p.apps.googleusercontent.com"
)

PROD_HOSTNAME = "neo-yukkuricraft"
IS_PROD_HOST = PROD_HOSTNAME in socket.gethostname()

CORS_ORIGIN = (
    "https://yakumo.yukkuricraft.net"
    if IS_PROD_HOST
    else "https://dev.yakumo.yukkuricraft.net"
)


HOST_PASSWD = "/etc/host-passwd"

DB_ENV_FILE = "secrets/db.env"

WHITELISTED_USERS_FILE = "secrets/whitelisted_google_sub_ids.txt"

ACCESS_TOKEN_DUR_MINS = 30

YC_TOKEN_AUTH_SCHEME = "YC-Token"

ENV_FOLDER: Path = Path("/app/env")

MIN_VALID_PROXY_PORT = 25600 if IS_PROD_HOST else 26600

MAX_VALID_PROXY_PORT = 25700 if IS_PROD_HOST else 26700
