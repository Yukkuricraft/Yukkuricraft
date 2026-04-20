from unittest import mock
import pytest  # type: ignore
import flask  # type: ignore

from src.api.lib.anti_abuse import client_ip_key


@pytest.fixture
def app():
    return flask.Flask(__name__)


def _request_ctx(app, headers=None, remote_addr="10.0.0.1"):
    headers = headers or {}
    return app.test_request_context("/", headers=headers, environ_base={"REMOTE_ADDR": remote_addr})


class TestClientIpKey:
    def test_uses_remote_addr_when_no_xff_header(self, app):
        with _request_ctx(app, remote_addr="203.0.113.5"):
            assert client_ip_key() == "203.0.113.5"

    def test_uses_remote_addr_when_xff_too_short(self, app):
        # Only one entry — fewer than TRUSTED_PROXY_HOPS (2). Treat as untrusted, fall back.
        with _request_ctx(app, headers={"X-Forwarded-For": "10.0.0.1"}, remote_addr="203.0.113.5"):
            assert client_ip_key() == "203.0.113.5"

    def test_extracts_third_from_right_when_two_proxy_hops(self, app):
        # client → ssl-term → nginx-proxy → api
        # XFF: client, ssl-term, nginx-proxy (rightmost two are proxies)
        with _request_ctx(
            app,
            headers={"X-Forwarded-For": "203.0.113.5, 10.0.0.10, 10.0.0.11"},
        ):
            assert client_ip_key() == "203.0.113.5"

    def test_handles_extra_hops_taking_third_from_right(self, app):
        # If for some reason a fourth hop exists (e.g. internal load balancer),
        # we still take the third-from-right by design.
        with _request_ctx(
            app,
            headers={"X-Forwarded-For": "1.1.1.1, 203.0.113.5, 10.0.0.10, 10.0.0.11"},
        ):
            assert client_ip_key() == "203.0.113.5"

    def test_strips_whitespace_around_entries(self, app):
        with _request_ctx(
            app,
            headers={"X-Forwarded-For": " 203.0.113.5 ,  10.0.0.10 , 10.0.0.11"},
        ):
            assert client_ip_key() == "203.0.113.5"

    def test_returns_unknown_when_remote_addr_missing(self, app):
        with _request_ctx(app, remote_addr=""):
            # Werkzeug coerces empty REMOTE_ADDR to None
            assert client_ip_key() == "unknown"


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
