"""Public, unauthenticated proxy endpoints for the yukkuricraft.net site.

Both endpoints are intentionally NOT decorated with `@validate_access_token`.
Defense in depth comes from the anti-abuse layers composed below
(`require_known_origin`) plus the host allow-list (ping) and circuit breaker
(uuid).
"""

import re

from flask import request  # type: ignore
from flask_openapi3 import APIBlueprint  # type: ignore

from src.api.blueprints import MinecraftPingPath, MinecraftUuidPath
from src.api.constants import CORS_ORIGINS
from src.api.lib.anti_abuse import require_known_origin
from src.api.lib.auth import return_cors_response
from src.api.lib.minecraft import (
    is_allowed_ping_host,
    lookup_uuid,
    ping,
)

minecraft_bp: APIBlueprint = APIBlueprint(
    "minecraft",
    __name__,
    url_prefix="/minecraft",
    # No abp_security — these endpoints are public by design.
)


@minecraft_bp.after_request
def _add_cors_headers(response):
    """Set Access-Control-Allow-Origin on every response from this blueprint.

    The minecraft handlers return raw dicts that Flask jsonifies, so they
    bypass `prepare_response()` (which is what sets CORS headers elsewhere
    in the API). This hook closes that gap. Reuses `CORS_ORIGINS` directly
    rather than calling auth.py's private `_pick_cors_origin` helper.
    """
    if CORS_ORIGINS == ["*"]:
        origin = "*"
    else:
        request_origin = request.headers.get("Origin", "")
        origin = request_origin if request_origin in CORS_ORIGINS else CORS_ORIGINS[0]

    response.headers.setdefault("Access-Control-Allow-Origin", origin)
    if origin != "*":
        response.headers.setdefault("Vary", "Origin")
    return response


@minecraft_bp.route("/ping/<string:host>/<string:port>", methods=["OPTIONS"])
def ping_options_handler(host: str, port: str):
    return return_cors_response()


@minecraft_bp.get("/ping/<string:host>/<string:port>")
@require_known_origin
def ping_handler(path: MinecraftPingPath):
    """SLP-ping a Minecraft server. Host must be under MC_PING_ALLOWED_BASE_DOMAIN."""
    try:
        port_int = int(path.port)
    except ValueError:
        return {"error": "invalid port"}, 400
    if port_int < 1 or port_int > 65535:
        return {"error": "invalid port"}, 400
    if not path.host or not path.host.strip():
        return {"error": "invalid host"}, 400
    if not is_allowed_ping_host(path.host):
        return {"error": "host not allowed"}, 403

    return ping(path.host, port_int), 200


_UUID_HEX_RE = re.compile(r"^[0-9a-fA-F]{32}$")


@minecraft_bp.route("/uuid/<string:uuid>", methods=["OPTIONS"])
def uuid_options_handler(uuid: str):
    return return_cors_response()


@minecraft_bp.get("/uuid/<string:uuid>")
@require_known_origin
def uuid_handler(path: MinecraftUuidPath):
    """Resolve a Minecraft username from a UUID via Mojang sessionserver."""
    normalized = path.uuid.replace("-", "")
    if not _UUID_HEX_RE.match(normalized):
        return {"error": "invalid uuid"}, 400
    return lookup_uuid(normalized), 200
