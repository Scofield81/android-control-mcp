"""Tesztek a gyarto/modell kompatibilitasi adatbazishoz - a legfontosabb elv:
ismeretlen modellre None (unknown), SOHA nem talalunk ki tamogatast."""

from __future__ import annotations

from android_control_mcp.rescue import compat_db


def test_lookup_known_pixel_8_returns_supported_wired_video():
    entry = compat_db.lookup("Google", "Pixel 8 Pro")
    assert entry is not None
    assert entry.wired_video_output == "supported"
    assert entry.displayport_alt_mode == "supported"


def test_lookup_xiaomi_15t_shows_otg_without_video_output():
    """A legfontosabb dokumentalt pelda: OTG-tamogatasbol NEM kovetkezik
    video-kimenet - a 15T-nek van OTG-je, de nincs vezetekes video-ja."""
    entry = compat_db.lookup("Xiaomi", "15T")
    assert entry is not None
    assert entry.wired_video_output == "unsupported"
    assert "otg" in entry.aoa_otg_note.lower() or entry.aoa_otg_note


def test_lookup_unknown_manufacturer_returns_none():
    assert compat_db.lookup("TotallyUnknownBrand", "Model X9000") is None


def test_lookup_unknown_model_of_known_manufacturer_returns_none():
    assert compat_db.lookup("Google", "Pixel 3") is None


def test_lookup_empty_input_returns_none():
    assert compat_db.lookup("", "") is None


def test_all_entries_have_source_and_verified_date():
    entries = compat_db.all_entries()
    assert len(entries) > 0
    for entry in entries:
        assert entry.source, f"{entry.manufacturer}/{entry.model_pattern} nincs forras nelkul"
        assert entry.verified_date
