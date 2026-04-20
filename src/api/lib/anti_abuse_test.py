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
