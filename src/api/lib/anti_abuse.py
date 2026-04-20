from flask import request  # type: ignore

from src.api.constants import TRUSTED_PROXY_HOPS


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
