"""Celzott regressziós teszt arra a hibara, amit a review talalt: az
usb_host ertek korabban tevesen 'supported' volt pusztan attol, hogy az ADB
mukodott (holott az ADB Wi-Fi-n keresztul is mukodhet, ami semmit nem mond a
telefon USB Host kepesserol). Most a tenyleges Android system feature-lista
('pm list features') donti el - ezt itt mock-olt ADB-valaszokkal ellenorizzuk,
valodi eszkoz nelkul is."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from android_control_mcp.adb import DeviceEntry
from android_control_mcp.rescue.capabilities import probe_capabilities


def _authorized_device():
    return [DeviceEntry(serial="emulator-5554", state="device")]


def test_usb_host_supported_when_feature_present():
    with patch("android_control_mcp.rescue.capabilities.list_devices",
               new=AsyncMock(return_value=_authorized_device())), \
         patch("android_control_mcp.rescue.capabilities.run_shell", new=AsyncMock()) as mock_shell:

        async def fake_run_shell(command, *, serial=None, timeout=30.0):
            if "getprop" in command:
                return "Google\nPixel 8 Pro\n15\n"
            if "pm list features" in command:
                return "feature:android.hardware.usb.host\nfeature:android.hardware.wifi\n"
            return ""

        mock_shell.side_effect = fake_run_shell
        report = asyncio.run(probe_capabilities())

    assert report.usb_host == "supported"


def test_usb_host_unsupported_when_feature_absent():
    """A LEGFONTOSABB eset: az ADB mukodik (authorized), DE a feature-lista
    NEM tartalmazza a usb.host-ot - ekkor 'unsupported', NEM 'supported'
    (ez volt a hiba: korabban puszta ADB-mukodesbol 'supported'-et allitott)."""
    with patch("android_control_mcp.rescue.capabilities.list_devices",
               new=AsyncMock(return_value=_authorized_device())), \
         patch("android_control_mcp.rescue.capabilities.run_shell", new=AsyncMock()) as mock_shell:

        async def fake_run_shell(command, *, serial=None, timeout=30.0):
            if "getprop" in command:
                return "SomeVendor\nSomeModel\n13\n"
            if "pm list features" in command:
                return "feature:android.hardware.wifi\nfeature:android.hardware.camera\n"
            return ""

        mock_shell.side_effect = fake_run_shell
        report = asyncio.run(probe_capabilities())

    assert report.usb_host == "unsupported"
    # Ha a usb.accessory feature is hianyzik, az AOA HID is biztosan nem mukodik.
    assert report.usb_accessory == "unsupported"
    assert report.aoa_hid == "unsupported"


def test_usb_host_stays_unknown_without_adb():
    """Ha nincs ADB, nem talalunk ki semmit - usb_host marad 'unknown'."""
    with patch("android_control_mcp.rescue.capabilities.list_devices",
               new=AsyncMock(return_value=[])):
        report = asyncio.run(probe_capabilities())

    assert report.usb_host == "unknown"
    assert report.aoa_hid == "unknown"
