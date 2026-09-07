"""Celzott regressziós teszt a 'network_status' tool egy valos eszkozon
(Xiaomi Redmi 9A, Android 10, WiFi kikapcsolva/nincs IP) feltart hibajara:
a 'grep inet' szandekosan nem-nulla kilepesi kodot ad, ha nincs talalat -
ez NEM hiba, de korabban az egesz tool-t elbuktatta egy AdbError-ral."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from mcp.server.fastmcp import FastMCP

from android_control_mcp.adb import AdbError
from android_control_mcp.tools import device as device_tools


def _register() -> dict:
    mcp = FastMCP("test")
    device_tools.register(mcp)
    return {t.name: t.fn for t in mcp._tool_manager.list_tools()}


def test_network_status_handles_no_wifi_ip_gracefully():
    """Ha a 'grep inet' nem talal semmit (wifi kikapcsolva/nincs IP), a
    tool-nak NEM szabad AdbError-t dobnia - ezt kell tennie: jelezze, hogy
    nincs IP, es folytassa a dumpsys wifi lekerdezessel."""
    tools = _register()
    network_status = tools["network_status"]

    async def fake_run_shell(command, *, serial=None, timeout=30.0):
        if "grep inet" in command:
            raise AdbError("")  # valodi eszkozon: grep exit 1, ures stderr
        if command == "dumpsys wifi":
            return "Wi-Fi is enabled\n"
        raise AssertionError(f"Varatlan parancs: {command}")

    async def run():
        with patch("android_control_mcp.tools.device.run_shell", new=fake_run_shell), \
             patch("android_control_mcp.tools.common.run_shell", new=fake_run_shell), \
             patch("android_control_mcp.tools.device.resolve_serial",
                   new=AsyncMock(return_value="fake-serial")):
            return await network_status(serial="fake-serial")

    result = asyncio.run(run())
    assert "nincs" in result.lower()
    assert "AdbError" not in result


def test_network_status_still_reports_ip_when_present():
    """Ha VAN IP, a tool azt megjelenitse, ne a 'nincs' agat."""
    tools = _register()
    network_status = tools["network_status"]

    async def fake_run_shell(command, *, serial=None, timeout=30.0):
        if "grep inet" in command:
            return "    inet 192.168.1.42/24 brd 192.168.1.255 scope global wlan0"
        if command == "dumpsys wifi":
            return "Wi-Fi is enabled\n"
        raise AssertionError(f"Varatlan parancs: {command}")

    async def run():
        with patch("android_control_mcp.tools.device.run_shell", new=fake_run_shell), \
             patch("android_control_mcp.tools.common.run_shell", new=fake_run_shell), \
             patch("android_control_mcp.tools.device.resolve_serial",
                   new=AsyncMock(return_value="fake-serial")):
            return await network_status(serial="fake-serial")

    result = asyncio.run(run())
    assert "192.168.1.42" in result
