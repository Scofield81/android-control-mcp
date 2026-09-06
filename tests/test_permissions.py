from __future__ import annotations

import pytest

from android_control_mcp.config import CONFIG, Mode
from android_control_mcp.permissions import (
    RISK_APP_CLEAR_DATA,
    RISK_APP_UNINSTALL,
    RISK_INSTALL_UNKNOWN_APK,
    RISK_REBOOT,
    RISK_REBOOT_BOOTLOADER,
    RISK_SHELL_RUN,
    PermissionDenied,
    RiskLevel,
    require_mode,
)


@pytest.fixture(autouse=True)
def _restore_config():
    original = CONFIG.mode
    yield
    CONFIG.mode = original


def test_require_mode_passes_when_current_mode_sufficient():
    CONFIG.mode = Mode.ADMIN
    require_mode(Mode.NORMAL, what="teszt muvelet")  # nem szabad kivetelt dobnia


def test_require_mode_passes_on_exact_match():
    CONFIG.mode = Mode.NORMAL
    require_mode(Mode.NORMAL, what="teszt muvelet")


def test_require_mode_blocks_when_current_mode_insufficient():
    CONFIG.mode = Mode.SAFE
    with pytest.raises(PermissionDenied):
        require_mode(Mode.ADMIN, what="teszt muvelet")


@pytest.mark.parametrize("risk_const", [
    RISK_APP_UNINSTALL, RISK_APP_CLEAR_DATA, RISK_INSTALL_UNKNOWN_APK,
    RISK_REBOOT, RISK_REBOOT_BOOTLOADER, RISK_SHELL_RUN,
])
def test_risk_constants_are_valid_level_reason_pairs(risk_const):
    level, reason = risk_const
    assert isinstance(level, RiskLevel)
    assert isinstance(reason, str) and reason
