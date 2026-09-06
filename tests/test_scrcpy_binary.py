"""Tesztek a hivatalos scrcpy binaris felismeresehez.

A tesztkornyezetben NINCS telepitve scrcpy - ez a leggyakoribb (alap)
allapot, es pontosan ezt tesztelik: hogy 'detect_scrcpy' ilyenkor SOHA nem
dob kivetelt, hanem egy hasznalhato, telepitesi utmutatot tartalmazo
'ScrcpyInfo(available=False, ...)'-t ad vissza."""

from __future__ import annotations

import asyncio

from android_control_mcp.rescue.scrcpy_binary import detect_scrcpy


def test_detect_scrcpy_reports_unavailable_when_not_installed():
    info = asyncio.run(detect_scrcpy())
    assert info.available is False
    assert info.version is None
    assert "scrcpy" in info.detail.lower()
    assert "github.com/genymobile" in info.detail.lower()


def test_detect_scrcpy_with_nonexistent_explicit_path_falls_back_gracefully():
    info = asyncio.run(detect_scrcpy(explicit_path="C:/nonexistent/path/scrcpy.exe"))
    assert info.available is False
    assert info.detail  # nem ures - konkret uzenetet ad
