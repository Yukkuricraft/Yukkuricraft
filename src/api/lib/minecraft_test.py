import pytest  # type: ignore

from src.api.lib.minecraft import is_allowed_ping_host


class TestIsAllowedPingHost:
    def test_accepts_exact_base_domain(self):
        assert is_allowed_ping_host("yukkuricraft.net") is True

    def test_accepts_subdomain(self):
        assert is_allowed_ping_host("play.yukkuricraft.net") is True

    def test_accepts_deeper_subdomain(self):
        assert is_allowed_ping_host("play.eu.yukkuricraft.net") is True

    def test_rejects_unrelated_host(self):
        assert is_allowed_ping_host("mc.hypixel.net") is False

    def test_rejects_host_with_base_domain_in_middle(self):
        assert is_allowed_ping_host("yukkuricraft.net.evil.example") is False

    def test_rejects_evil_lookalike_without_dot(self):
        # Critical case — the leading dot in the suffix prevents this bypass.
        assert is_allowed_ping_host("evil-yukkuricraft.net") is False

    def test_rejects_empty_host(self):
        assert is_allowed_ping_host("") is False

    def test_rejects_whitespace_only_host(self):
        assert is_allowed_ping_host("   ") is False

    def test_is_case_insensitive(self):
        # DNS is case-insensitive; treat "Play.YukkuriCraft.NET" as valid.
        assert is_allowed_ping_host("Play.YukkuriCraft.NET") is True


from src.api.lib.minecraft import flatten_description


class TestFlattenDescription:
    def test_plain_string_passes_through(self):
        assert flatten_description("hello world") == "hello world"

    def test_simple_component_with_text(self):
        assert flatten_description({"text": "hello"}) == "hello"

    def test_component_with_color(self):
        assert flatten_description({"text": "hello", "color": "red"}) == "\u00a7chello"

    def test_component_with_bold_and_color(self):
        # Bold + color: emit both prefix codes before text.
        result = flatten_description({"text": "hi", "color": "blue", "bold": True})
        # Order is color then style, but exact order isn't part of MC's spec —
        # both must be present before "hi".
        assert "\u00a7l" in result and "\u00a79" in result and result.endswith("hi")

    def test_component_with_extras(self):
        component = {
            "text": "Hello ",
            "extra": [
                {"text": "World", "color": "green"},
                {"text": "!", "color": "yellow", "bold": True},
            ],
        }
        out = flatten_description(component)
        assert out.startswith("Hello ")
        assert "\u00a7aWorld" in out  # green = a
        assert "\u00a7e" in out and "\u00a7l" in out and out.endswith("!")  # yellow + bold

    def test_unknown_color_is_skipped(self):
        # Don't emit a code for colors we don't recognize.
        assert flatten_description({"text": "hi", "color": "fuchsia"}) == "hi"

    def test_handles_missing_text_key(self):
        # A component with only `extra` and no own text.
        component = {"extra": [{"text": "child"}]}
        assert flatten_description(component) == "child"

    def test_returns_empty_for_unexpected_shape(self):
        assert flatten_description(None) == ""
        assert flatten_description(123) == ""

    def test_uses_motd_to_minecraft_when_available(self):
        # mcstatus v11+ wraps the description in a Motd object. We must use
        # its built-in `.to_minecraft()` method rather than treating it as a
        # plain object.
        class FakeMotd:
            def to_minecraft(self):
                return "\u00a7cfake red"

        assert flatten_description(FakeMotd()) == "\u00a7cfake red"


import time as time_module
from src.api.lib.minecraft import TTLCache


class TestTTLCache:
    def test_get_returns_none_on_miss(self):
        c = TTLCache(maxsize=10, success_ttl=60.0, error_ttl=10.0)
        assert c.get("k") is None

    def test_set_and_get_within_ttl(self, mocker):
        fake_time = mocker.patch("src.api.lib.minecraft.time.monotonic")
        fake_time.return_value = 1000.0
        c = TTLCache(maxsize=10, success_ttl=60.0, error_ttl=10.0)
        c.set("k", {"value": 1}, is_error=False)
        fake_time.return_value = 1030.0  # 30s later, < 60s TTL
        assert c.get("k") == {"value": 1}

    def test_success_entry_expires_after_success_ttl(self, mocker):
        fake_time = mocker.patch("src.api.lib.minecraft.time.monotonic")
        fake_time.return_value = 1000.0
        c = TTLCache(maxsize=10, success_ttl=60.0, error_ttl=10.0)
        c.set("k", {"value": 1}, is_error=False)
        fake_time.return_value = 1061.0
        assert c.get("k") is None

    def test_error_entry_expires_after_error_ttl(self, mocker):
        fake_time = mocker.patch("src.api.lib.minecraft.time.monotonic")
        fake_time.return_value = 1000.0
        c = TTLCache(maxsize=10, success_ttl=60.0, error_ttl=10.0)
        c.set("k", {"error": "timeout"}, is_error=True)
        fake_time.return_value = 1011.0  # past 10s error TTL
        assert c.get("k") is None
        # And before that:
        fake_time.return_value = 1005.0
        c.set("k", {"error": "timeout"}, is_error=True)
        assert c.get("k") == {"error": "timeout"}

    def test_eviction_at_maxsize(self, mocker):
        fake_time = mocker.patch("src.api.lib.minecraft.time.monotonic")
        fake_time.return_value = 1000.0
        c = TTLCache(maxsize=2, success_ttl=60.0, error_ttl=10.0)
        c.set("a", {"v": 1}, is_error=False)
        c.set("b", {"v": 2}, is_error=False)
        c.set("c", {"v": 3}, is_error=False)
        # Should hold at most 2 entries — oldest evicted.
        present = sum(1 for k in ("a", "b", "c") if c.get(k) is not None)
        assert present == 2


import socket
from unittest import mock

from src.api.lib.minecraft import ping, _ping_cache


@pytest.fixture(autouse=True)
def clear_caches():
    _ping_cache._store.clear()
    yield
    _ping_cache._store.clear()


class TestPing:
    def test_returns_normalized_success(self, mocker):
        fake_status = mock.Mock()
        fake_status.description = {"text": "MOTD"}
        fake_status.icon = "data:image/png;base64,abc"
        fake_status.players.max = 100
        fake_status.players.online = 7
        fake_player = mock.Mock()
        fake_player.id = "11111111-2222-3333-4444-555555555555"
        fake_player.name = "remiscarlet"
        fake_status.players.sample = [fake_player]
        fake_status.version.name = "Paper 1.20.1"
        fake_status.version.protocol = 763
        fake_status.latency = 42.7

        fake_server = mock.Mock()
        fake_server.status.return_value = fake_status
        mocker.patch(
            "src.api.lib.minecraft.JavaServer.lookup", return_value=fake_server
        )

        result = ping("play.yukkuricraft.net", 25565)
        assert result == {
            "description": "MOTD",
            "favicon": "data:image/png;base64,abc",
            "players": {
                "max": 100,
                "online": 7,
                "sample": [
                    {"id": "11111111-2222-3333-4444-555555555555", "name": "remiscarlet"}
                ],
            },
            "version": {"name": "Paper 1.20.1", "protocol": 763},
            "latency": 42.7,
        }

    def test_handles_missing_player_sample(self, mocker):
        fake_status = mock.Mock()
        fake_status.description = "plain MOTD"
        fake_status.icon = None
        fake_status.players.max = 100
        fake_status.players.online = 0
        fake_status.players.sample = None
        fake_status.version.name = "Paper 1.20.1"
        fake_status.version.protocol = 763
        fake_status.latency = 5.0

        fake_server = mock.Mock()
        fake_server.status.return_value = fake_status
        mocker.patch("src.api.lib.minecraft.JavaServer.lookup", return_value=fake_server)

        result = ping("play.yukkuricraft.net", 25565)
        assert result["players"]["sample"] == []
        assert result["favicon"] is None
        assert result["description"] == "plain MOTD"

    def test_returns_timeout_error(self, mocker):
        fake_server = mock.Mock()
        fake_server.status.side_effect = socket.timeout()
        mocker.patch("src.api.lib.minecraft.JavaServer.lookup", return_value=fake_server)
        assert ping("play.yukkuricraft.net", 25565) == {"error": "timeout"}

    def test_returns_refused_error(self, mocker):
        fake_server = mock.Mock()
        fake_server.status.side_effect = ConnectionRefusedError()
        mocker.patch("src.api.lib.minecraft.JavaServer.lookup", return_value=fake_server)
        assert ping("play.yukkuricraft.net", 25565) == {"error": "refused"}

    def test_returns_invalid_host_for_dns_failure(self, mocker):
        # mcstatus surfaces DNS failures as socket.gaierror.
        fake_server = mock.Mock()
        fake_server.status.side_effect = socket.gaierror()
        mocker.patch("src.api.lib.minecraft.JavaServer.lookup", return_value=fake_server)
        assert ping("nope.yukkuricraft.net", 25565) == {"error": "invalid host"}

    def test_caches_success(self, mocker):
        fake_status = mock.Mock()
        fake_status.description = "ok"
        fake_status.icon = None
        fake_status.players.max = 1
        fake_status.players.online = 0
        fake_status.players.sample = []
        fake_status.version.name = "v"
        fake_status.version.protocol = 0
        fake_status.latency = 0.0
        fake_server = mock.Mock()
        fake_server.status.return_value = fake_status
        lookup_mock = mocker.patch(
            "src.api.lib.minecraft.JavaServer.lookup", return_value=fake_server
        )

        ping("play.yukkuricraft.net", 25565)
        ping("play.yukkuricraft.net", 25565)
        assert lookup_mock.call_count == 1  # second call served from cache

    def test_caches_errors_separately(self, mocker):
        fake_server = mock.Mock()
        fake_server.status.side_effect = socket.timeout()
        mocker.patch(
            "src.api.lib.minecraft.JavaServer.lookup", return_value=fake_server
        )

        first = ping("play.yukkuricraft.net", 25565)
        second = ping("play.yukkuricraft.net", 25565)
        assert first == second == {"error": "timeout"}


import requests as _requests

from src.api.lib.minecraft import lookup_uuid, _uuid_cache, mojang_breaker


@pytest.fixture(autouse=True)
def clear_uuid_state():
    _uuid_cache._store.clear()
    mojang_breaker.record_success()  # forces closed state
    yield
    _uuid_cache._store.clear()
    mojang_breaker.record_success()


def _mock_response(status_code, json_body=None):
    resp = mock.Mock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json.return_value = json_body
    return resp


class TestLookupUuid:
    def test_returns_normalized_success(self, mocker):
        body = {"id": "069a79f444e94726a5befca90e38aaf5", "name": "Notch"}
        mocker.patch(
            "src.api.lib.minecraft.requests.get",
            return_value=_mock_response(200, body),
        )
        result = lookup_uuid("069a79f444e94726a5befca90e38aaf5")
        assert result == {"id": "069a79f444e94726a5befca90e38aaf5", "name": "Notch"}

    def test_returns_not_found_for_204(self, mocker):
        mocker.patch(
            "src.api.lib.minecraft.requests.get", return_value=_mock_response(204)
        )
        assert lookup_uuid("00000000000000000000000000000000") == {"error": "not found"}

    def test_returns_not_found_for_404(self, mocker):
        mocker.patch(
            "src.api.lib.minecraft.requests.get", return_value=_mock_response(404)
        )
        assert lookup_uuid("00000000000000000000000000000000") == {"error": "not found"}

    def test_returns_rate_limited_for_429(self, mocker):
        mocker.patch(
            "src.api.lib.minecraft.requests.get", return_value=_mock_response(429)
        )
        assert lookup_uuid("069a79f444e94726a5befca90e38aaf5") == {"error": "rate limited"}

    def test_429_records_failure_on_circuit_breaker(self, mocker):
        mocker.patch(
            "src.api.lib.minecraft.requests.get", return_value=_mock_response(429)
        )
        # Trigger threshold (3) consecutive 429s — breaker should open.
        for _ in range(3):
            lookup_uuid(f"{_:032x}")
        assert mojang_breaker.is_open() is True

    def test_open_breaker_short_circuits_without_calling_mojang(self, mocker):
        get_mock = mocker.patch("src.api.lib.minecraft.requests.get")
        # Force breaker open without calling Mojang
        for _ in range(3):
            mojang_breaker.record_failure()
        assert mojang_breaker.is_open()

        result = lookup_uuid("069a79f444e94726a5befca90e38aaf5")
        assert result == {"error": "rate limited"}
        get_mock.assert_not_called()

    def test_caches_success(self, mocker):
        body = {"id": "069a79f444e94726a5befca90e38aaf5", "name": "Notch"}
        get_mock = mocker.patch(
            "src.api.lib.minecraft.requests.get",
            return_value=_mock_response(200, body),
        )
        lookup_uuid("069a79f444e94726a5befca90e38aaf5")
        lookup_uuid("069a79f444e94726a5befca90e38aaf5")
        assert get_mock.call_count == 1

    def test_caches_not_found(self, mocker):
        get_mock = mocker.patch(
            "src.api.lib.minecraft.requests.get", return_value=_mock_response(204)
        )
        lookup_uuid("00000000000000000000000000000000")
        lookup_uuid("00000000000000000000000000000000")
        assert get_mock.call_count == 1

    def test_unexpected_exception_returns_error_string(self, mocker):
        mocker.patch(
            "src.api.lib.minecraft.requests.get",
            side_effect=_requests.ConnectionError("boom"),
        )
        result = lookup_uuid("069a79f444e94726a5befca90e38aaf5")
        assert "error" in result and "boom" in result["error"]
