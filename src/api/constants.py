from pathlib import Path

G_CLIENT_ID = (
    "1084736521175-2b5rrrpcs422qdc5458dhisdsj8auo0p.apps.googleusercontent.com"
)

CORS_ORIGIN = "https://yakumo2.yukkuricraft.net"

DB_ENV_FILE = "secrets/db.env"

WHITELISTED_USERS_FILE = "secrets/whitelisted_google_sub_ids.txt"

ACCESS_TOKEN_DUR_MINS = 1

YC_TOKEN_AUTH_SCHEME = "YC-Token"

ENV_FOLDER: Path = Path("/app/env")

MIN_VALID_PROXY_PORT = 25600
MAX_VALID_PROXY_PORT = 25700
