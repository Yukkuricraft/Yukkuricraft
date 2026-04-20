import time
from collections import deque
from functools import wraps
from typing import Callable, Deque

from flask import request  # type: ignore
from flask_limiter import Limiter  # type: ignore

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


class CircuitBreaker:
    """Simple in-memory circuit breaker.

    State machine:
    - **closed:** all calls allowed, failures recorded.
    - **open:** trips when `failure_threshold` failures occur within
      `window_secs`. While open, `is_open()` returns True for `open_secs`.
    - **half-open:** after `open_secs` elapses, `is_open()` returns False
      once (the "trial" request). The next `record_failure()` re-opens for
      another full `open_secs`; a `record_success()` resets to closed.

    All times use `time.monotonic()` so they're immune to wall-clock jumps.
    Single-threaded reasoning is fine — gunicorn/gevent serializes Python-level
    ops within a single greenlet, and per-worker imprecision (multiple workers
    each tracking their own breaker state) is accepted at this scale.
    """

    def __init__(self, failure_threshold: int, window_secs: float, open_secs: float):
        self.failure_threshold = failure_threshold
        self.window_secs = window_secs
        self.open_secs = open_secs
        self._failures: Deque[float] = deque()
        self._opened_at: float | None = None
        self._half_open: bool = False

    def _prune_old_failures(self, now: float) -> None:
        cutoff = now - self.window_secs
        while self._failures and self._failures[0] < cutoff:
            self._failures.popleft()

    def is_open(self) -> bool:
        now = time.monotonic()
        if self._opened_at is not None:
            if now - self._opened_at < self.open_secs:
                return True
            # open_secs elapsed — transition to half-open. Clear failure
            # history; flag the trial state so the next record_failure() can
            # re-open immediately.
            self._opened_at = None
            self._failures.clear()
            self._half_open = True
            return False
        return False

    def record_failure(self) -> None:
        now = time.monotonic()
        if self._half_open:
            # Half-open trial failed — re-open immediately.
            self._opened_at = now
            self._half_open = False
            return
        self._failures.append(now)
        self._prune_old_failures(now)
        if len(self._failures) >= self.failure_threshold:
            self._opened_at = now

    def record_success(self) -> None:
        self._failures.clear()
        self._opened_at = None
        self._half_open = False


# Single shared limiter instance. Decorators on routes (`@limiter.limit(...)`)
# register their limits against this. The default in-memory backend is
# per-worker, which is acceptable at current scale (effective limit is
# N_workers x stated_limit). Swap to Redis later via `storage_uri="redis://..."`
# without changing any decorators.
limiter = Limiter(
    key_func=client_ip_key,
    default_limits=[],  # no global default — each protected endpoint declares its own
)
