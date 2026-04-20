"""Public, unauthenticated proxy endpoints for the yukkuricraft.net site.

Both endpoints are intentionally NOT decorated with `@validate_access_token`.
Defense in depth comes from the anti-abuse layers composed below
(`require_known_origin`, `@limiter.limit`) plus the host allow-list (ping)
and circuit breaker (uuid).
"""

import re

from flask_openapi3 import APIBlueprint  # type: ignore

from src.api.lib.anti_abuse import limiter, require_known_origin
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


@minecraft_bp.get("/ping/<string:host>/<string:port>")
@require_known_origin
@limiter.limit("30/minute; 5/second")
def ping_handler(host: str, port: str):
    """SLP-ping a Minecraft server. Host must be under MC_PING_ALLOWED_BASE_DOMAIN."""
    try:
        port_int = int(port)
    except ValueError:
        return {"error": "invalid port"}, 400
    if port_int < 1 or port_int > 65535:
        return {"error": "invalid port"}, 400
    if not host or not host.strip():
        return {"error": "invalid host"}, 400
    if not is_allowed_ping_host(host):
        return {"error": "host not allowed"}, 403

    return ping(host, port_int), 200


_UUID_HEX_RE = re.compile(r"^[0-9a-fA-F]{32}$")


@minecraft_bp.get("/uuid/<string:uuid>")
@require_known_origin
@limiter.limit("60/minute; 10/second")
def uuid_handler(uuid: str):
    """Resolve a Minecraft username from a UUID via Mojang sessionserver."""
    normalized = uuid.replace("-", "")
    if not _UUID_HEX_RE.match(normalized):
        return {"error": "invalid uuid"}, 400
    return lookup_uuid(normalized), 200
