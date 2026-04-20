"""Minecraft proxy endpoint helpers — SLP ping, Mojang UUID lookup, caching.

These are public, unauthenticated endpoints. Anti-abuse is layered on at the
blueprint level (see `src/api/lib/anti_abuse.py`).
"""

import time
from collections import OrderedDict
from typing import Any, Optional, Tuple

from src.api.constants import MC_PING_ALLOWED_BASE_DOMAIN


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
