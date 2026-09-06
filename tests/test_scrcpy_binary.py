"""Tesztek a hivatalos scrcpy binaris felismeresehez.

Minden teszt szandekosan IZOLALJA a felismeresi utvonalakat (shutil.which,
glob.glob, Path.is_file) - korabban ezek a tesztek KOZVETLENUL a futtato gep
tenyleges allapotara tamaszkodtak (csak azert 'mukodtek', mert a fejlesztoi
gepen eppen nem volt telepitve scrcpy). Ez egy valodi hiba volt: miutan egy
valos eszkozos teszthez ténylegesen telepitve lett a hivatalos scrcpy
(winget install Genymobile.scrcpy), mindket teszt elbukott, mert a
'nincs telepitve' allitas mar nem volt igaz - lasd REAL_DEVICE_TESTING.local.md
2026-09-06-i bejegyzeset. Innentol a tesztek a gep tenyleges allapotatol
fuggetlenul, determinisztikusan futnak."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

from android_control_mcp.rescue.scrcpy_binary import detect_scrcpy


def test_detect_scrcpy_reports_unavailable_when_not_installed(monkeypatch):
    monkeypatch.delenv("ANDROID_CONTROL_SCRCPY_PATH", raising=False)
    with patch("android_control_mcp.rescue.scrcpy_binary.shutil.which", return_value=None), \
         patch("android_control_mcp.rescue.scrcpy_binary.glob.glob", return_value=[]), \
         patch("android_control_mcp.rescue.scrcpy_binary.Path.is_file", return_value=False):
        info = asyncio.run(detect_scrcpy())
    assert info.available is False
    assert info.version is None
    assert "scrcpy" in info.detail.lower()
    assert "github.com/genymobile" in info.detail.lower()


def test_detect_scrcpy_with_nonexistent_explicit_path_falls_back_gracefully(monkeypatch):
    monkeypatch.delenv("ANDROID_CONTROL_SCRCPY_PATH", raising=False)
    with patch("android_control_mcp.rescue.scrcpy_binary.shutil.which", return_value=None), \
         patch("android_control_mcp.rescue.scrcpy_binary.glob.glob", return_value=[]), \
         patch("android_control_mcp.rescue.scrcpy_binary.Path.is_file", return_value=False):
        info = asyncio.run(detect_scrcpy(explicit_path="C:/nonexistent/path/scrcpy.exe"))
    assert info.available is False
    assert info.detail  # nem ures - konkret uzenetet ad


def test_detect_scrcpy_reads_android_control_scrcpy_path_env_var(monkeypatch, tmp_path):
    """Regresszios teszt: korabban az ANDROID_CONTROL_SCRCPY_PATH kornyezeti
    valtozot a hibauzeneg AJANLOTTA, de a kod sosem olvasta ki - a valtozo
    beallitasa semmit nem valtoztatott volna. Valos eszkozos teszttel derult
    ki (2026-09-06)."""
    fake_scrcpy = tmp_path / "scrcpy.exe"
    fake_scrcpy.write_text("fake")
    monkeypatch.setenv("ANDROID_CONTROL_SCRCPY_PATH", str(fake_scrcpy))

    async def fake_get_version(executable):
        return "scrcpy 4.1 (fake)" if executable == str(fake_scrcpy) else None

    with patch("android_control_mcp.rescue.scrcpy_binary.shutil.which", return_value=None), \
         patch("android_control_mcp.rescue.scrcpy_binary._try_get_version",
               side_effect=fake_get_version):
        info = asyncio.run(detect_scrcpy())

    assert info.available is True
    assert info.executable == str(fake_scrcpy)


def test_detect_scrcpy_explicit_path_takes_priority_over_env_var(monkeypatch, tmp_path):
    """Ha mind fuggveny-parameter, mind kornyezeti valtozo meg van adva, a
    fuggveny-parameter (explicit_path) elsobbseget kell elveznie."""
    param_scrcpy = tmp_path / "param" / "scrcpy.exe"
    param_scrcpy.parent.mkdir()
    param_scrcpy.write_text("fake")
    env_scrcpy = tmp_path / "env" / "scrcpy.exe"
    env_scrcpy.parent.mkdir()
    env_scrcpy.write_text("fake")
    monkeypatch.setenv("ANDROID_CONTROL_SCRCPY_PATH", str(env_scrcpy))

    async def fake_get_version(executable):
        return "scrcpy 4.1 (fake)"

    with patch("android_control_mcp.rescue.scrcpy_binary.shutil.which", return_value=None), \
         patch("android_control_mcp.rescue.scrcpy_binary._try_get_version",
               side_effect=fake_get_version):
        info = asyncio.run(detect_scrcpy(explicit_path=str(param_scrcpy)))

    assert info.executable == str(param_scrcpy)
