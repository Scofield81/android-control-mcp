"""Tesztek a kepesseg-felismeres logikajahoz.

Ezekben a tesztekben NINCS csatlakoztatott Android eszkoz - ez a
'device_capabilities'/'rescue_probe' szempontjabol a leggyakoribb, alap
allapot torott kijelzo/sose engedelyezett ADB eseten. A teszt pontosan azt
ellenorzi, hogy ilyenkor minden ADB-fuggo mezo 'unknown'/'unavailable'
marad (SOHA nem talal ki adatot), es a compat_db-bol jovo hint-alapu
lekerdezes attol meg mukodik."""

from __future__ import annotations

import asyncio

from android_control_mcp.rescue.capabilities import probe_capabilities, recommend_path


def test_probe_without_any_device_reports_unavailable_adb():
    report = asyncio.run(probe_capabilities())
    assert report.adb_state == "unavailable"
    assert report.adb_authorized == "unknown"
    # ADB nelkul a scrcpy_mirror_possible sem lehet 'supported'.
    assert report.scrcpy_mirror_possible != "supported"


def test_probe_with_manufacturer_hint_uses_compat_db_even_without_adb():
    report = asyncio.run(probe_capabilities(manufacturer_hint="Google", model_hint="Pixel 8 Pro"))
    assert report.adb_state == "unavailable"  # meg mindig nincs eszkoz
    assert report.wired_video_output == "supported"  # de a hint alapjan ez mar tudhato
    assert report.compat_source


def test_probe_with_unknown_model_hint_stays_unknown():
    report = asyncio.run(probe_capabilities(manufacturer_hint="Nokia", model_hint="3310"))
    assert report.wired_video_output == "unknown"


def test_recommend_path_never_crashes_on_all_unknown_report():
    report = asyncio.run(probe_capabilities())
    recommendation = recommend_path(report)
    assert isinstance(recommendation, str) and recommendation
