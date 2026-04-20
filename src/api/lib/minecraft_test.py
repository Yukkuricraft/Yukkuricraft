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
