from pathlib import Path
import os

CONFIGURATION_TYPE = os.getenv("CONFIGURATION_TYPE", "local")
if CONFIGURATION_TYPE is None:
    raise RuntimeError(
        "CONFIGURATION_TYPE was not set! Must be local, dev, prod. Aborting."
    )

IS_PROD = CONFIGURATION_TYPE == "prod"
IS_DEV = CONFIGURATION_TYPE == "dev"
IS_LOCAL = CONFIGURATION_TYPE == "local"

# Public-site origins that are also allowed to call the /minecraft/* endpoints.
# Kept separate from the dashboard origins so the lists can diverge later if needed.
PUBLIC_SITE_ORIGINS = [
    "https://www.yukkuricraft.net",
    "https://yukkuricraft.net",
]

if IS_LOCAL:
    G_CLIENT_ID = "some-arbitrary-client-id"
    CORS_ORIGINS = ["*"]  # wildcard for local dev — not a real allowlist; guard for this before using `in`
    MIN_VALID_PROXY_PORT = 26600
    MAX_VALID_PROXY_PORT = 26700
    API_HOST = "api.localhost"
    HOSTNAME = "localhost"
elif IS_DEV:
    G_CLIENT_ID = (
        "1084736521175-2b5rrrpcs422qdc5458dhisdsj8auo0p.apps.googleusercontent.com"
    )
    CORS_ORIGINS = ["https://dev.yakumo.yukkuricraft.net"] + PUBLIC_SITE_ORIGINS
    MIN_VALID_PROXY_PORT = 26600
    MAX_VALID_PROXY_PORT = 26700
    API_HOST = "dev.api.yukkuricraft.net"
    HOSTNAME = "yukkuricraft.net"
elif IS_PROD:
    G_CLIENT_ID = (
        "1084736521175-2b5rrrpcs422qdc5458dhisdsj8auo0p.apps.googleusercontent.com"
    )
    CORS_ORIGINS = ["https://yakumo.yukkuricraft.net"] + PUBLIC_SITE_ORIGINS
    MIN_VALID_PROXY_PORT = 25600
    MAX_VALID_PROXY_PORT = 25700
    API_HOST = "api.yukkuricraft.net"
    HOSTNAME = "yukkuricraft.net"
else:
    raise RuntimeError(
        f"Found running on an unknown environment! CONFIGURATION_TYPE was '${CONFIGURATION_TYPE}'"
    )

HOST_PASSWD = "/etc/host-passwd"
WHITELISTED_USERS_FILE = "secrets/whitelisted_google_sub_ids.txt"
ACCESS_TOKEN_DUR_MINS = 30
YC_TOKEN_AUTH_SCHEME = "Bearer"
ENV_FOLDER: Path = Path("/app/env")

BACKUP_CONTENT_ROOT: str = "/worlds-bindmount"
"""We technically can't assume this will _always_ be the backup root but
we have to hardcode it in a few places like template files and shellscripts.

It's probably not gonna change.
But if it does, we should figure out a better way to share the value across api, templates, scripts etc.
"""

# Anti-abuse / minecraft proxy
MC_PING_ALLOWED_BASE_DOMAIN = "yukkuricraft.net"
