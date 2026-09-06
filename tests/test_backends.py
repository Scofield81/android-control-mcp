"""Tesztek a scrcpy/ADB input-backend valasztasi logikajahoz.

Fontos: ezekben a tesztekben SEM a 'scrcpy-client' csomag, SEM valodi eszkoz
nincs jelen - pontosan ezt a (leggyakoribb, alapertelmezett) allapotot
tesztelik: hogy a rendszer ilyenkor mindig es kizarolag a bizonyitottan
mukodo ADB-utat valasztja, es SOHA nem dob kivetelt emiatt kifele."""

from __future__ import annotations

import asyncio

import android_control_mcp.backends as backends_module
from android_control_mcp.backends import AdbInputBackend, get_backend, scrcpy_requested


def _reset_backend_state(monkeypatch):
    monkeypatch.setattr(backends_module, "_backend_cache", {})
    monkeypatch.setattr(backends_module, "_scrcpy_globally_disabled", False)


def test_scrcpy_requested_false_by_default(monkeypatch):
    monkeypatch.delenv("ANDROID_CONTROL_SCRCPY", raising=False)
    assert scrcpy_requested() is False


def test_scrcpy_requested_true_when_env_set(monkeypatch):
    monkeypatch.setenv("ANDROID_CONTROL_SCRCPY", "1")
    assert scrcpy_requested() is True
    monkeypatch.delenv("ANDROID_CONTROL_SCRCPY", raising=False)


def test_get_backend_returns_adb_when_scrcpy_not_requested(monkeypatch):
    monkeypatch.delenv("ANDROID_CONTROL_SCRCPY", raising=False)
    _reset_backend_state(monkeypatch)
    backend = asyncio.run(get_backend("emulator-5554"))
    assert isinstance(backend, AdbInputBackend)


def test_get_backend_falls_back_to_adb_when_scrcpy_package_missing(monkeypatch):
    """A tesztkornyezetben nincs telepitve a 'scrcpy-client' csomag - ez a
    tipikus/alapertelmezett eset egy olyan gepen, ahol senki nem kapcsolta be
    kulon a kiserleti gyorsitast. Ilyenkor a bekapcsolt env-valtozo ELLENERE
    is csendben ADB-re kell esnie, kivetel nelkul."""
    monkeypatch.setenv("ANDROID_CONTROL_SCRCPY", "1")
    _reset_backend_state(monkeypatch)

    backend = asyncio.run(get_backend("emulator-5554"))

    assert isinstance(backend, AdbInputBackend)
    monkeypatch.delenv("ANDROID_CONTROL_SCRCPY", raising=False)


def test_get_backend_caches_result_per_serial(monkeypatch):
    monkeypatch.delenv("ANDROID_CONTROL_SCRCPY", raising=False)
    _reset_backend_state(monkeypatch)
    b1 = asyncio.run(get_backend("dev1"))
    b2 = asyncio.run(get_backend("dev1"))
    assert b1 is b2
