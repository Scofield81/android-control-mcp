"""Az MCP szerver osszeallitasa.

Minden tool-modul `register(mcp)` fuggvenyet meghivjuk. A szerver stdio
transzporton fut (lokalis MCP kliens indit egy alfolyamatkent), de HTTP-re is
valthato az ANDROID_CONTROL_TRANSPORT=http kornyezeti valtozoval.
"""

from __future__ import annotations

import os
import sys

from mcp.server.fastmcp import FastMCP

from .config import CONFIG
from .tools import REGISTRARS

INSTRUCTIONS = """\
Android Control MCP - Android eszkozok (telefon/tablet, USB vagy wifi ADB-n
keresztul) teljes koru vezerlese: UI-automatizalas, kepernyokep/felvetel,
alkalmazas- es fajlkezeles, naplok, ertesitesek.

FONTOS HATAR: ez az eszkoz NEM kepes es NEM is a celja kepernyozar/jelszo
megkeruleset. Minden muvelethez az eszkoznek korabban mar jova kellett hagynia
a szamitogepet ('USB hibakereses engedelyezese' parbeszed a telefon
kepernyojen) - ez az Android sajat biztonsagi mechanizmusa, nem ezen szerver
korlatja.

Engedely-modok (a szerver egy modban fut - lasd 'device_info'/'set_mode'):
  SAFE   - csak olvasas: eszkoz-info, kepernyokep, ui_dump, naplok, fajlolvasas
  NORMAL - + koppintas/gepeles/gesztusok, alkalmazas-inditas/leallitas, fajlmuveletek
  ADMIN  - + alkalmazas eltavolitasa/adattorlese, APK telepites, ujrainditas,
           teljes mentes, tetszoleges shell parancs

Ket vedelmi reteg dolgozik:
  1) A mod-kapu eldonti, egy tool egyaltalan futhat-e.
  2) A visszafordithatatlan/adatvesztessel jaro muveletek (uninstall, adattorles,
     ujrainditas, torles, ismeretlen APK telepitese) a modtol fuggetlenul
     interaktiv megerositest kernek a felhasznalotol.

Ajanlott munkafolyamat kepernyo-interakciohoz:
  1) 'ui_dump' - milyen elemek lathatoak, hol vannak (nem kell kepernyot 'nezni')
  2) 'tap'/'swipe'/'type_text' a talalt koordinatakkal
  3) 'wait_for_text' a kovetkezo allapot kivarasahoz (nem fix alvas)
  4) ha egy UI sajatos/grafikus (jatek, video): 'screenshot' a tenyleges latashoz

Tobb eszkoz eseten mindig add meg a 'serial' parametert (lasd 'device_list').
"""


def build_server() -> FastMCP:
    mcp = FastMCP("android_control_mcp", instructions=INSTRUCTIONS)
    for register in REGISTRARS:
        register(mcp)
    return mcp


mcp = build_server()


def _startup_banner() -> None:
    tool_count = "?"
    try:
        tool_count = len(mcp._tool_manager._tools)  # type: ignore[attr-defined]
    except Exception:
        pass
    print(
        f"[android-control-mcp] indul | mod={CONFIG.mode.value.upper()} "
        f"| toolok={tool_count} | config={CONFIG.config_path} "
        f"| adb={CONFIG.adb_path} "
        f"| alap-eszkoz={CONFIG.default_serial or '(automatikus)'}",
        file=sys.stderr,
        flush=True,
    )


def run() -> None:
    _startup_banner()
    transport = os.environ.get("ANDROID_CONTROL_TRANSPORT", "stdio").lower()
    if transport == "http":
        port = int(os.environ.get("ANDROID_CONTROL_PORT", "8001"))
        mcp.settings.port = port
        mcp.settings.host = os.environ.get("ANDROID_CONTROL_HOST", "127.0.0.1")
        mcp.run(transport="streamable-http")
    else:
        mcp.run()
