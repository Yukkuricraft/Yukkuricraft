from functools import wraps
from typing import Callable

from flask import request  # type: ignore

from src.api.constants import CORS_ORIGINS, TRUSTED_PROXY_HOPS


def client_ip_key() -> str:
    """flask-limiter `key_func` — returns the real client IP behind our proxy chain.

    Topology: client → SSL terminator → nginx-proxy → API. Both proxies append
    to X-Forwarded-For, so the rightmost TRUSTED_PROXY_HOPS entries are proxy
    hops and the entry just before them is the real client.

    If XFF is missing or shorter than expected (local dev, direct hit), we fall
    back to request.remote_addr.
    """
    xff = request.headers.get("X-Forwarded-For", "")
    parts = [p.strip() for p in xff.split(",") if p.strip()]
    if len(parts) > TRUSTED_PROXY_HOPS:
        return parts[-(TRUSTED_PROXY_HOPS + 1)]
    return request.remote_addr or "unknown"


def require_known_origin(func: Callable) -> Callable:
    """Reject requests whose `Origin` header is not in `CORS_ORIGINS`.

    Reuses the CORS allow-list as the single source of truth for "who's
    allowed to call us". Trivially forgeable with curl `-H "Origin: ..."`,
    so this is a cheap filter against lazy/automated abuse, not a security
    boundary; the per-IP rate limit and circuit breaker are the real
    defenses.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if CORS_ORIGINS == ["*"]:
            return func(*args, **kwargs)
        origin = request.headers.get("Origin", "")
        if origin not in CORS_ORIGINS:
            return {"error": "forbidden origin"}, 403
        return func(*args, **kwargs)

    return wrapper
