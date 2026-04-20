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
