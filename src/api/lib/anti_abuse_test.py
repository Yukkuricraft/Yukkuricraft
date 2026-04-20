from unittest import mock
import pytest  # type: ignore
import flask  # type: ignore

from src.api.lib.anti_abuse import require_known_origin


def _make_app_with_protected_route(monkeypatch, allowed_origins):
    monkeypatch.setattr("src.api.lib.anti_abuse.CORS_ORIGINS", allowed_origins)
    app = flask.Flask(__name__)

    @app.route("/protected")
    @require_known_origin
    def protected():
        return {"ok": True}

    return app


class TestRequireKnownOrigin:
    def test_allows_request_with_known_origin(self, monkeypatch):
        app = _make_app_with_protected_route(
            monkeypatch, ["https://www.yukkuricraft.net"]
        )
        client = app.test_client()
        resp = client.get("/protected", headers={"Origin": "https://www.yukkuricraft.net"})
        assert resp.status_code == 200
        assert resp.get_json() == {"ok": True}

    def test_rejects_request_with_unknown_origin(self, monkeypatch):
        app = _make_app_with_protected_route(
            monkeypatch, ["https://www.yukkuricraft.net"]
        )
        client = app.test_client()
        resp = client.get("/protected", headers={"Origin": "https://evil.example"})
        assert resp.status_code == 403
        assert resp.get_json() == {"error": "forbidden origin"}

    def test_rejects_request_with_no_origin(self, monkeypatch):
        app = _make_app_with_protected_route(
            monkeypatch, ["https://www.yukkuricraft.net"]
        )
        client = app.test_client()
        resp = client.get("/protected")
        assert resp.status_code == 403
        assert resp.get_json() == {"error": "forbidden origin"}

    def test_wildcard_origins_allows_anything(self, monkeypatch):
        # Local-dev convention: CORS_ORIGINS == ["*"] means accept any (or no) Origin.
        app = _make_app_with_protected_route(monkeypatch, ["*"])
        client = app.test_client()
        assert client.get("/protected").status_code == 200
        assert client.get("/protected", headers={"Origin": "https://anything"}).status_code == 200


import time as time_module

from src.api.lib.anti_abuse import CircuitBreaker


class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker(failure_threshold=3, window_secs=60, open_secs=300)
        assert cb.is_open() is False

    def test_does_not_open_below_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, window_secs=60, open_secs=300)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open() is False

    def test_opens_when_threshold_reached_in_window(self, mocker):
        fake_time = mocker.patch("src.api.lib.anti_abuse.time.monotonic")
        fake_time.return_value = 1000.0
        cb = CircuitBreaker(failure_threshold=3, window_secs=60, open_secs=300)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open() is True

    def test_failures_outside_window_do_not_count(self, mocker):
        fake_time = mocker.patch("src.api.lib.anti_abuse.time.monotonic")
        cb = CircuitBreaker(failure_threshold=3, window_secs=60, open_secs=300)
        fake_time.return_value = 1000.0
        cb.record_failure()
        fake_time.return_value = 1500.0  # 500s later — outside the 60s window
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open() is False  # only 2 failures within window

    def test_record_success_resets_failures(self, mocker):
        fake_time = mocker.patch("src.api.lib.anti_abuse.time.monotonic")
        fake_time.return_value = 1000.0
        cb = CircuitBreaker(failure_threshold=3, window_secs=60, open_secs=300)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open() is False  # success cleared the prior failures

    def test_open_state_expires_after_open_secs(self, mocker):
        fake_time = mocker.patch("src.api.lib.anti_abuse.time.monotonic")
        fake_time.return_value = 1000.0
        cb = CircuitBreaker(failure_threshold=2, window_secs=60, open_secs=300)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open() is True
        fake_time.return_value = 1305.0  # 305s later — past the 300s open window
        assert cb.is_open() is False  # half-open: one request is allowed through

    def test_half_open_failure_reopens_breaker(self, mocker):
        fake_time = mocker.patch("src.api.lib.anti_abuse.time.monotonic")
        fake_time.return_value = 1000.0
        cb = CircuitBreaker(failure_threshold=2, window_secs=60, open_secs=300)
        cb.record_failure()
        cb.record_failure()
        fake_time.return_value = 1305.0
        assert cb.is_open() is False  # half-open
        cb.record_failure()  # the trial request failed
        assert cb.is_open() is True  # re-opened immediately

    def test_half_open_success_closes_breaker(self, mocker):
        fake_time = mocker.patch("src.api.lib.anti_abuse.time.monotonic")
        fake_time.return_value = 1000.0
        cb = CircuitBreaker(failure_threshold=2, window_secs=60, open_secs=300)
        cb.record_failure()
        cb.record_failure()
        fake_time.return_value = 1305.0
        assert cb.is_open() is False  # half-open
        cb.record_success()  # the trial request succeeded
        # Subsequent failures need to reach the threshold again from zero
        cb.record_failure()
        assert cb.is_open() is False
