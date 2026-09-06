"""Gyarto/modell kompatibilitasi adatbazis - bovitheto JSON strukturaban.

FONTOS: ez az adatbazis SZANDEKOSAN kicsi es konzervativ. Minden bejegyzeshez
forras es ellenorzes datuma tartozik. Ha egy modell nincs benne, a valasz
'unknown' - SOHA nem talalunk ki tamogatast pusztan az USB-C csatlakozo
vagy az Android verzio alapjan (USB Host/OTG kepesseg NEM jelenti azt, hogy
az adott telefon vezetekes video-kimenetet is tamog).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parent / "data" / "devices.json"
"""A csomagon BELUL van (nem a projekt gyokereben), hogy sima 'pip install'
(nem csak editable) eseten is bekeruljon a wheel-be - lasd pyproject.toml
'[tool.hatch.build.targets.wheel]' -> force-include."""


@dataclass
class DeviceCompatEntry:
    manufacturer: str
    model_pattern: str
    wired_video_output: str = "unknown"  # supported | unsupported | unknown
    displayport_alt_mode: str = "unknown"
    samsung_dex_wired: str = "unknown"
    samsung_dex_pc: str = "unknown"
    aoa_otg_note: str = ""
    source: str = ""
    verified_date: str = ""
    note: str = ""


def _load_db() -> list[DeviceCompatEntry]:
    if not _DB_PATH.exists():
        return []
    try:
        raw = json.loads(_DB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    entries = []
    for item in raw.get("devices", []):
        entries.append(DeviceCompatEntry(
            manufacturer=item.get("manufacturer", ""),
            model_pattern=item.get("model_pattern", ""),
            wired_video_output=item.get("wired_video_output", "unknown"),
            displayport_alt_mode=item.get("displayport_alt_mode", "unknown"),
            samsung_dex_wired=item.get("samsung_dex_wired", "unknown"),
            samsung_dex_pc=item.get("samsung_dex_pc", "unknown"),
            aoa_otg_note=item.get("aoa_otg_note", ""),
            source=item.get("source", ""),
            verified_date=item.get("verified_date", ""),
            note=item.get("note", ""),
        ))
    return entries


_DB_CACHE: list[DeviceCompatEntry] | None = None


def lookup(manufacturer: str, model: str) -> DeviceCompatEntry | None:
    """Modell-egyezes kereses (case-insensitive, reszleges/regex mintaval).
    None-t ad vissza, ha nincs ismert bejegyzes - ez SZANDEKOS, nem hiba."""
    global _DB_CACHE
    if _DB_CACHE is None:
        _DB_CACHE = _load_db()

    manufacturer_l = (manufacturer or "").strip().lower()
    model_l = (model or "").strip().lower()
    if not manufacturer_l and not model_l:
        return None

    for entry in _DB_CACHE:
        if entry.manufacturer.lower() != manufacturer_l:
            continue
        try:
            if re.search(entry.model_pattern, model_l, re.IGNORECASE):
                return entry
        except re.error:
            if entry.model_pattern.lower() in model_l:
                return entry
    return None


def all_entries() -> list[DeviceCompatEntry]:
    global _DB_CACHE
    if _DB_CACHE is None:
        _DB_CACHE = _load_db()
    return list(_DB_CACHE)
