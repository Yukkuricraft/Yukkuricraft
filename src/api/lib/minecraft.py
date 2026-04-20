"""Minecraft proxy endpoint helpers — SLP ping, Mojang UUID lookup, caching.

These are public, unauthenticated endpoints. Anti-abuse is layered on at the
blueprint level (see `src/api/lib/anti_abuse.py`).
"""

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
