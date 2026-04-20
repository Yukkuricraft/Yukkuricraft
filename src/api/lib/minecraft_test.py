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
