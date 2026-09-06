"""Konfiguracio betoltese: alap ertekek, config.json, kornyezeti valtozok.

A sorrend (kesobbi felulirja a korabbit): beepitett alapertelmezes -> config
fajl -> kornyezeti valtozok. Igy a config fajl megosztja a beallitasokat
tobb gepen, a kornyezeti valtozok pedig gepenkent finomhangolhatnak (pl. CI).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Mode(str, Enum):
    SAFE = "safe"
    NORMAL = "normal"
    ADMIN = "admin"


_LEVELS = {Mode.SAFE: 0, Mode.NORMAL: 1, Mode.ADMIN: 2}


def level_value(mode: Mode) -> int:
    return _LEVELS[mode]


def _default_config_path() -> Path:
    base = os.environ.get("APPDATA") or os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "android-control-mcp" / "config.json"


def _default_audit_log_path() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "android-control-mcp" / "audit.log"


@dataclass
class AppConfig:
    mode: Mode = Mode.NORMAL
    """Az AKTUALIS mod - ez valtozik 'set_mode' hivasra. Sose hasonlitsd ezt
    ahhoz, hogy meddig szabad felfele menni - arra a max_mode van."""
    max_mode: Mode = Mode.NORMAL
    """A szerver inditasakor rogzitett FELSO HATAR (env/config alapjan). 'set_mode'
    sosem tud ennel magasabbra menni, fuggetlenul attol, hogy 'mode' pillanatnyilag
    mit mutat - igy egy ADMIN->SAFE->ADMIN oda-vissza valtas is korrekt marad."""
    auto_approve: bool = False
    audit_log: Path | None = None
    default_serial: str | None = None
    """Ha tobb eszkoz van csatlakoztatva es a hivo nem ad meg 'serial'-t, ezt hasznaljuk."""
    adb_path: str = "adb"
    config_path: Path = field(default_factory=_default_config_path)
    screenshot_max_bytes: int = 8 * 1024 * 1024
    """Biztonsagi felso hatar egy kepernyokep/fajl meretere, hogy egy hibas eszkoz
    ne tudjon veletlenul GB-os valaszt kuldeni az MCP klienshez."""


def _load_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _parse_mode(value: object, fallback: Mode) -> Mode:
    if isinstance(value, str):
        try:
            return Mode(value.lower())
        except ValueError:
            pass
    return fallback


def load_config() -> AppConfig:
    cfg = AppConfig()

    config_path_env = os.environ.get("ANDROID_CONTROL_CONFIG")
    cfg.config_path = Path(config_path_env) if config_path_env else _default_config_path()
    file_data = _load_file(cfg.config_path)

    cfg.mode = _parse_mode(file_data.get("mode"), cfg.mode)
    cfg.auto_approve = bool(file_data.get("auto_approve", cfg.auto_approve))
    cfg.default_serial = file_data.get("default_serial", cfg.default_serial)
    cfg.adb_path = file_data.get("adb_path", cfg.adb_path)
    if file_data.get("audit_log"):
        cfg.audit_log = Path(file_data["audit_log"]).expanduser()

    # Kornyezeti valtozok felulirjak a fajlt.
    cfg.mode = _parse_mode(os.environ.get("ANDROID_CONTROL_MODE"), cfg.mode)
    if "ANDROID_CONTROL_AUTO_APPROVE" in os.environ:
        cfg.auto_approve = os.environ["ANDROID_CONTROL_AUTO_APPROVE"] in ("1", "true", "True")
    if os.environ.get("ANDROID_CONTROL_DEFAULT_SERIAL"):
        cfg.default_serial = os.environ["ANDROID_CONTROL_DEFAULT_SERIAL"]
    if os.environ.get("ANDROID_CONTROL_ADB_PATH"):
        cfg.adb_path = os.environ["ANDROID_CONTROL_ADB_PATH"]
    if os.environ.get("ANDROID_CONTROL_AUDIT_LOG"):
        cfg.audit_log = Path(os.environ["ANDROID_CONTROL_AUDIT_LOG"]).expanduser()

    if cfg.audit_log is None:
        cfg.audit_log = _default_audit_log_path()

    cfg.max_mode = cfg.mode

    return cfg


CONFIG = load_config()
