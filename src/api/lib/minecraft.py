"""Minecraft proxy endpoint helpers — SLP ping, Mojang UUID lookup, caching.

These are public, unauthenticated endpoints. Anti-abuse is layered on at the
blueprint level (see `src/api/lib/anti_abuse.py`).
"""

import socket
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple

import requests

from mcstatus import JavaServer  # type: ignore

from src.common.logger_setup import logger

from src.api.constants import MC_PING_ALLOWED_BASE_DOMAIN
from src.api.lib.anti_abuse import CircuitBreaker


def is_allowed_ping_host(host: str) -> bool:
    """True iff `host` is the base domain or a subdomain of it.

    The leading dot in the suffix check is load-bearing: it prevents
    `evil-yukkuricraft.net` style bypasses where the attacker registers a
    domain that ends with the base domain string but isn't actually under
    it. Comparison is case-insensitive (DNS is).
    """
    if not host or not host.strip():
        return False
    host_lc = host.strip().lower()
    base = MC_PING_ALLOWED_BASE_DOMAIN.lower()
    return host_lc == base or host_lc.endswith("." + base)


# Minecraft chat color → § code. See https://minecraft.wiki/w/Formatting_codes
_COLOR_CODES = {
    "black": "0",
    "dark_blue": "1",
    "dark_green": "2",
    "dark_aqua": "3",
    "dark_red": "4",
    "dark_purple": "5",
    "gold": "6",
    "gray": "7",
    "dark_gray": "8",
    "blue": "9",
    "green": "a",
    "aqua": "b",
    "red": "c",
    "light_purple": "d",
    "yellow": "e",
    "white": "f",
}

_STYLE_CODES = {
    "obfuscated": "k",
    "bold": "l",
    "strikethrough": "m",
    "underlined": "n",
    "italic": "o",
}

_SECTION = "\u00a7"  # §


def _emit(component: dict) -> str:
    """Emit `§<color><styles...><text>` for a single component (no recursion)."""
    out = ""
    color = component.get("color")
    if color in _COLOR_CODES:
        out += _SECTION + _COLOR_CODES[color]
    for name, code in _STYLE_CODES.items():
        if component.get(name):
            out += _SECTION + code
    out += str(component.get("text", ""))
    return out


def flatten_description(desc: Any) -> str:
    """Flatten a Minecraft chat-component tree (or plain string) to legacy
    §-prefixed text.

    SLP responses use either a plain string or a nested component dict
    `{text, color?, bold?, ..., extra: [...]}`. The Vue caller expects a
    single string and calls its own `parseMCCodes` on it, which only
    understands the legacy `§<code>` format.
    """
    if isinstance(desc, str):
        return desc
    if not isinstance(desc, dict):
        return ""
    out = _emit(desc)
    for child in desc.get("extra", []) or []:
        if isinstance(child, dict):
            out += flatten_description(child)
        elif isinstance(child, str):
            out += child
    return out


class TTLCache:
    """Tiny FIFO-ish TTL cache with separate success/error TTLs.

    Why not `cachetools.TTLCache`: that library uses a single TTL per cache
    instance. We want different TTLs for success vs error entries (so failed
    upstream calls recover quickly). Implementation is small enough that
    rolling our own is cheaper than two parallel cachetools instances.
    """

    def __init__(self, maxsize: int, success_ttl: float, error_ttl: float):
        self.maxsize = maxsize
        self.success_ttl = success_ttl
        self.error_ttl = error_ttl
        # value: (payload, expires_at_monotonic)
        self._store: "OrderedDict[str, Tuple[Any, float]]" = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        payload, expires = entry
        if time.monotonic() >= expires:
            del self._store[key]
            return None
        return payload

    def set(self, key: str, payload: Any, is_error: bool) -> None:
        ttl = self.error_ttl if is_error else self.success_ttl
        expires = time.monotonic() + ttl
        if key in self._store:
            del self._store[key]
        self._store[key] = (payload, expires)
        while len(self._store) > self.maxsize:
            self._store.popitem(last=False)


PING_TIMEOUT_SECS = 3.0
_PING_CACHE_MAXSIZE = 512
_PING_SUCCESS_TTL = 60.0
_PING_ERROR_TTL = 10.0

_ping_cache = TTLCache(
    maxsize=_PING_CACHE_MAXSIZE,
    success_ttl=_PING_SUCCESS_TTL,
    error_ttl=_PING_ERROR_TTL,
)


def _normalize_player_sample(sample) -> list:
    if not sample:
        return []
    return [{"id": p.id, "name": p.name} for p in sample]


def ping(host: str, port: int) -> dict:
    """Server List Ping a Minecraft server and normalize the response.

    Returns a success dict matching the api.minetools.eu shape, or
    `{"error": "<reason>"}` on failure. Failure reasons:
    - `"timeout"`     — socket timeout
    - `"refused"`     — TCP connection refused
    - `"invalid host"` — DNS lookup failed
    - exception message — anything else

    Caller is responsible for the host allow-list check (see
    `is_allowed_ping_host`) — this function does not enforce it.
    """
    cache_key = f"{host}:{port}"
    cached = _ping_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        server = JavaServer.lookup(f"{host}:{port}", timeout=PING_TIMEOUT_SECS)
        status = server.status()
    except socket.timeout:
        result = {"error": "timeout"}
        _ping_cache.set(cache_key, result, is_error=True)
        return result
    except ConnectionRefusedError:
        result = {"error": "refused"}
        _ping_cache.set(cache_key, result, is_error=True)
        return result
    except socket.gaierror:
        result = {"error": "invalid host"}
        _ping_cache.set(cache_key, result, is_error=True)
        return result
    except Exception as e:
        logger.exception("Unexpected error pinging %s:%d", host, port)
        result = {"error": str(e) or e.__class__.__name__}
        _ping_cache.set(cache_key, result, is_error=True)
        return result

    result = {
        "description": flatten_description(status.description),
        "favicon": status.favicon,
        "players": {
            "max": status.players.max,
            "online": status.players.online,
            "sample": _normalize_player_sample(status.players.sample),
        },
        "version": {
            "name": status.version.name,
            "protocol": status.version.protocol,
        },
        "latency": status.latency,
    }
    _ping_cache.set(cache_key, result, is_error=False)
    return result


UUID_TIMEOUT_SECS = 3.0
_UUID_CACHE_MAXSIZE = 512
_UUID_SUCCESS_TTL = 24 * 60 * 60.0  # 24 hours
_UUID_ERROR_TTL = 5 * 60.0  # 5 minutes

_uuid_cache = TTLCache(
    maxsize=_UUID_CACHE_MAXSIZE,
    success_ttl=_UUID_SUCCESS_TTL,
    error_ttl=_UUID_ERROR_TTL,
)

# One breaker for Mojang sessionserver. 3 consecutive 429s in a 60s window
# trip it for 5 minutes.
mojang_breaker = CircuitBreaker(
    failure_threshold=3, window_secs=60.0, open_secs=5 * 60.0
)

_MOJANG_PROFILE_URL = "https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"


def lookup_uuid(uuid_no_dashes: str) -> dict:
    """Look up a Minecraft username from a UUID via Mojang sessionserver.

    Returns `{"id": "...", "name": "..."}` on success, or `{"error": "..."}`
    where error is one of: `"not found"`, `"rate limited"`, or an exception
    string.

    Caller is responsible for input validation (32 hex chars, dashes
    stripped).
    """
    cached = _uuid_cache.get(uuid_no_dashes)
    if cached is not None:
        return cached

    if mojang_breaker.is_open():
        # Don't even try — Mojang is throttling us. Don't cache (we want to
        # try again as soon as the breaker half-opens).
        return {"error": "rate limited"}

    try:
        resp = requests.get(
            _MOJANG_PROFILE_URL.format(uuid=uuid_no_dashes),
            timeout=UUID_TIMEOUT_SECS,
        )
    except Exception as e:
        logger.exception("Unexpected error calling Mojang sessionserver")
        result = {"error": str(e) or e.__class__.__name__}
        _uuid_cache.set(uuid_no_dashes, result, is_error=True)
        return result

    if resp.status_code == 200:
        body = resp.json()
        result = {"id": body.get("id", ""), "name": body.get("name", "")}
        _uuid_cache.set(uuid_no_dashes, result, is_error=False)
        mojang_breaker.record_success()
        return result
    if resp.status_code in (204, 404):
        result = {"error": "not found"}
        _uuid_cache.set(uuid_no_dashes, result, is_error=True)
        mojang_breaker.record_success()  # 404 isn't a Mojang failure mode
        return result
    if resp.status_code == 429:
        mojang_breaker.record_failure()
        # Don't cache — we want immediate retry once the breaker permits it.
        return {"error": "rate limited"}

    # Anything else: treat as a generic error.
    result = {"error": f"upstream {resp.status_code}"}
    _uuid_cache.set(uuid_no_dashes, result, is_error=True)
    return result
