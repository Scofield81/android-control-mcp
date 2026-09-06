"""Kepernyokep, kepernyofelvetel es UI-hierarchia ('latas' a modell szamara).

Az ui_dump az Android sajat uiautomator eszkozet hasznalja, ami az
Accessibility-hez hasonloan strukturalt informaciot ad az aktualisan lathato
elemekrol (szoveg, resource-id, koordinatak, kattinthato-e) - igy a modellnek
nem kell kepfelismeressel (OCR/CV) kitalalnia, hova kell koppintani.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from mcp.server.fastmcp import Image

from ..adb import resolve_serial, run_adb, run_adb_checked, run_shell
from ..audit import audit
from ..formatting import truncate
from .common import SerialArg


def register(mcp) -> None:

    @mcp.tool()
    async def screenshot(serial: SerialArg = None):
        """Kepernyokep keszitese az eszkozrol, PNG kepkent visszaadva.

        Igy a modell szo szerint 'latja' az aktualis kepernyot - hasznos amikor
        az ui_dump nem eleg (pl. jatek, video, egyedi rajzolt UI).
        """
        real_serial = await resolve_serial(serial)
        result = await run_adb(["exec-out", "screencap", "-p"], serial=real_serial,
                                timeout=20.0, binary=True)
        if result.returncode != 0:
            raise RuntimeError(f"Kepernyokep sikertelen: {result.stderr.strip()}")
        data = result.stdout.encode("latin-1")
        audit("screenshot", serial=real_serial, bytes=len(data))
        return Image(data=data, format="png")

    @mcp.tool()
    async def screen_record(seconds: int = 5, serial: SerialArg = None):
        """Rovid (max 30 mp) kepernyofelvetel keszitese MP4 formatumban.

        Hasznos animaciok, atmenetek, jatekmenet visszanezesehez. A felvetel az
        eszkoz ideiglenes tarhelyere kerul, majd letoltodik es torlodik onnan.
        """
        seconds = max(1, min(30, int(seconds)))
        real_serial = await resolve_serial(serial)
        remote_path = "/sdcard/android_control_mcp_record.mp4"

        await run_adb_checked(
            ["shell", f"screenrecord --time-limit {seconds} {remote_path}"],
            serial=real_serial, timeout=seconds + 15,
        )
        result = await run_adb(["exec-out", "cat", remote_path], serial=real_serial,
                                timeout=30.0, binary=True)
        await run_shell(f"rm -f {remote_path}", serial=real_serial)

        if result.returncode != 0 or not result.stdout:
            raise RuntimeError("A kepernyofelvetel nem sikerult vagy ures lett.")

        data = result.stdout.encode("latin-1")
        audit("screen_record", serial=real_serial, seconds=seconds, bytes=len(data))
        # Az MCP kepen kivul nativan nem tamogat video-tipust minden kliens; a fajlt
        # ezert a hivo altal megadhato helyi utvonalra is le lehet menteni a
        # 'pull_file' tool-lal a felvetel utan (a remote_path mar torolve van, ezert
        # ez a tool a nyers meretet es egy figyelmeztetest ad vissza, ha tul nagy).
        if len(data) > 15 * 1024 * 1024:
            return (
                f"A felvetel elkeszult ({len(data) / 1024 / 1024:.1f} MB), de tul nagy ahhoz, "
                "hogy kozvetlenul visszakuldjuk. Hasznalj rovidebb 'seconds' erteket, vagy "
                "keszits inkabb tobb 'screenshot'-ot a fontos pillanatokrol."
            )
        import base64
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:video/mp4;base64,{b64}"

    @mcp.tool()
    async def ui_dump(serial: SerialArg = None, only_interactive: bool = True) -> str:
        """Az aktualis kepernyo UI-elemeinek strukturalt listaja (uiautomator).

        Minden elemhez megadja: szoveg, resource-id, osztaly, es a kozeppont
        koordinatait (amit a 'tap' tool-nak at lehet adni). Ez a legmegbizhatobb
        modja annak, hogy a modell tudja, hova koppintson - nem kell kepen
        'talalgatnia'. only_interactive=True eseten csak a kattinthato/szerkesztheto
        elemeket mutatja (rovidebb, attekinthetobb valasz).
        """
        real_serial = await resolve_serial(serial)
        remote_path = "/sdcard/android_control_mcp_dump.xml"
        await run_adb_checked(["shell", f"uiautomator dump {remote_path}"],
                               serial=real_serial, timeout=20.0)
        xml_text = await run_adb_checked(["exec-out", "cat", remote_path],
                                          serial=real_serial, timeout=15.0)
        await run_shell(f"rm -f {remote_path}", serial=real_serial)

        elements = _parse_ui_dump(xml_text, only_interactive=only_interactive)
        if not elements:
            return "Nem talalhato elem (ures kepernyo, vagy csak grafikus/jatek tartalom - probald a 'screenshot' tool-t)."
        return truncate("\n".join(elements))

    @mcp.tool()
    async def wait_for_text(text: str, timeout_seconds: int = 10, serial: SerialArg = None) -> str:
        """Var, amig egy adott szoveg megjelenik a kepernyon (ui_dump-ot ismetel).

        Hasznos, hogy az agent ne 'tuti 1 masodpercet' varjon minden lepes utan,
        hanem tenylegesen addig probalkozzon, amig a keresett UI elem meg nem
        jelenik (pl. betoltodik egy oldal), de legfeljebb timeout_seconds-ig.
        """
        import asyncio
        import time

        real_serial = await resolve_serial(serial)
        deadline = time.monotonic() + max(1, min(60, timeout_seconds))
        remote_path = "/sdcard/android_control_mcp_dump.xml"

        while time.monotonic() < deadline:
            await run_adb_checked(["shell", f"uiautomator dump {remote_path}"],
                                   serial=real_serial, timeout=15.0)
            xml_text = await run_adb_checked(["exec-out", "cat", remote_path],
                                              serial=real_serial, timeout=10.0)
            if text.lower() in xml_text.lower():
                await run_shell(f"rm -f {remote_path}", serial=real_serial)
                return f"Megtalalva: {text!r} megjelent a kepernyon."
            await asyncio.sleep(1.0)

        await run_shell(f"rm -f {remote_path}", serial=real_serial)
        return f"Idotullepes: {text!r} nem jelent meg {timeout_seconds} masodperc alatt."


def _parse_ui_dump(xml_text: str, *, only_interactive: bool) -> list[str]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    bounds_re = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
    lines: list[str] = []

    for node in root.iter("node"):
        text = node.get("text", "")
        desc = node.get("content-desc", "")
        res_id = node.get("resource-id", "")
        cls = node.get("class", "").rsplit(".", 1)[-1]
        clickable = node.get("clickable") == "true"
        editable = "EditText" in cls
        bounds = node.get("bounds", "")

        if only_interactive and not (clickable or editable):
            continue
        if not (text or desc or res_id):
            continue

        m = bounds_re.match(bounds)
        center = ""
        if m:
            x1, y1, x2, y2 = map(int, m.groups())
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            center = f"({cx},{cy})"

        label = text or desc or res_id.rsplit("/", 1)[-1]
        flags = "".join([
            "T" if editable else "",
            "C" if clickable else "",
        ])
        lines.append(f"[{flags}] {cls} \"{label}\" id={res_id or '-'} center={center}")

    return lines
