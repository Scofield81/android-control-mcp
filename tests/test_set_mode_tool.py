"""Vegponttol-vegpontig teszt a tenylegesen regisztralt 'set_mode' MCP tool-on
keresztul (nem csak a kulon ujraírt logikan) - ez igazolja, hogy a bugfix
tenylegesen a futo kodban is mukodik, nem csak a teszt sajat masolataban."""

from __future__ import annotations

import asyncio

import pytest

from android_control_mcp.config import CONFIG, Mode
from android_control_mcp.server import mcp


def _call_set_mode(mode: str) -> str:
    fn = mcp._tool_manager._tools["set_mode"].fn
    return asyncio.run(fn(mode=mode))


@pytest.fixture(autouse=True)
def _restore_config():
    original_mode, original_max = CONFIG.mode, CONFIG.max_mode
    yield
    CONFIG.mode, CONFIG.max_mode = original_mode, original_max


def test_admin_ceiling_allows_down_then_back_up():
    CONFIG.max_mode = Mode.ADMIN
    CONFIG.mode = Mode.ADMIN

    result = _call_set_mode("safe")
    assert "SAFE" in result
    assert CONFIG.mode == Mode.SAFE

    result = _call_set_mode("admin")
    assert "ADMIN" in result
    assert CONFIG.mode == Mode.ADMIN  # <- ez a regi kodban meghiusult volna


def test_normal_ceiling_blocks_admin():
    CONFIG.max_mode = Mode.NORMAL
    CONFIG.mode = Mode.NORMAL

    result = _call_set_mode("admin")
    assert "NEM valthato" in result
    assert CONFIG.mode == Mode.NORMAL  # valtozatlan maradt


def test_invalid_mode_name_rejected():
    CONFIG.max_mode = Mode.ADMIN
    CONFIG.mode = Mode.NORMAL

    result = _call_set_mode("superuser")
    assert "Ervenytelen mod" in result
    assert CONFIG.mode == Mode.NORMAL
