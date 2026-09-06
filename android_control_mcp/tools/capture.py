"""Kepernyokep, kepernyofelvetel es UI-hierarchia ('latas' a modell szamara).

Az ui_dump az Android sajat uiautomator eszkozet hasznalja, ami az
Accessibility-hez hasonloan strukturalt informaciot ad az aktualisan lathato
elemekrol (szoveg, resource-id, koordinatak, kattinthato-e) - igy a modellnek
nem kell kepfelismeressel (OCR/CV) kitalalnia, hova kell koppintani.

A tenyleges XML-parszolas es elem-strukturalas a common.py-ban van
(parse_ui_elements/find_matching_elements), hogy az elements.py szemantikus
tool-jai (tap_element, type_into, ...) ugyanazt a logikat hasznaljak.
"""

from __future__ import annotations

from mcp.server.fastmcp import Image

from ..adb import resolve_serial, run_adb, run_adb_checked, run_shell
from ..audit import audit
from ..formatting import truncate
from .common import (
    SerialArg,
    fetch_ui_dump_xml,
    format_element,
    parse_ui_elements,
)


def register(mcp) -> None:

    @mcp.tool()
    async def screenshot(serial: SerialArg = None):
        """Kepernyokep keszitese az eszkozrol, PNG kepkent visszaadva.

        Igy a modell szo szerint 'latja' az aktualis kepernyot - hasznos amikor
        az ui_dump nem eleg (pl. jatek, video, egyedi rajzolt UI, WebView/Canvas
        tartalom, amit az uiautomator nem lat elemenkent).
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

        Minden elemhez megadja: id (a 'tap_element'/'type_into' 'element_id'
        parameteret ez adja), szoveg, resource-id, osztaly, allapot-jelzok
        ([C]lickable/[T]ext-mezo/[E]nabled/[S]elected), es a kozeppont
        koordinatait. Ez a legmegbizhatobb modja annak, hogy a modell tudja,
        hova koppintson - de meg egyszerubb kozvetlenul a 'tap_element'/
        'find_element' tool-t hasznalni, ami mar el is vegzi a koordinata-
        szamolast. only_interactive=True eseten csak a kattinthato/szerkesztheto
        elemeket mutatja (rovidebb, attekinthetobb valasz).
        """
        xml_text, real_serial = await fetch_ui_dump_xml(serial)
        elements = parse_ui_elements(xml_text)
        if only_interactive:
            elements = [e for e in elements if e["clickable"] or e["editable"]]

        if not elements:
            return ("Nem talalhato hasznalhato elem (ures kepernyo, vagy csak grafikus/jatek/"
                    "WebView/Canvas tartalom, amit az uiautomator nem lat elemenkent). Probald "
                    "az 'ocr_screen' tool-t (ha az opcionalis OCR extra telepitve van), vagy a "
                    "'screenshot'-ot vizualis ellenorzeshez.")
        return truncate("\n".join(format_element(e) for e in elements))

    @mcp.tool()
    async def ocr_screen(lang: str = "eng", serial: SerialArg = None) -> str:
        """OCR-alapu szovegfelismeres a kepernyon - fallback, amikor az 'ui_dump'
        ures listat ad (jatek, WebView, Canvas, egyedi rajzolt UI).

        Opcionalis fuggoseget igenyel: 'pip install -e \".[ocr]\"' a projektben,
        plusz a Tesseract OCR motor rendszerszintu telepiteset. Ha ezek
        hianyoznak, vilagos utmutatast ad, mit kell telepiteni - nem hasal el.
        lang: Tesseract nyelvkod, tobb nyelvhez pl. 'eng+hun'.
        """
        from ..ocr import format_ocr_box, ocr_available, run_ocr

        available, message = ocr_available()
        if not available:
            return message

        real_serial = await resolve_serial(serial)
        result = await run_adb(["exec-out", "screencap", "-p"], serial=real_serial,
                                timeout=20.0, binary=True)
        if result.returncode != 0:
            return f"Kepernyokep sikertelen az OCR-hez: {result.stderr.strip()}"

        png_bytes = result.stdout.encode("latin-1")
        boxes = run_ocr(png_bytes, lang=lang)
        audit("ocr_screen", serial=real_serial, box_count=len(boxes), lang=lang)

        if not boxes:
            return "Az OCR nem talalt felismerheto szoveget a kepernyon."
        return truncate("\n".join(format_ocr_box(b) for b in boxes))

    @mcp.tool()
    async def wait_for_text(text: str, timeout_seconds: int = 10, serial: SerialArg = None) -> str:
        """Var, amig egy adott szoveg megjelenik a kepernyon (ui_dump-ot ismetel).

        Hasznos, hogy az agent ne 'tuti X masodpercet' varjon minden lepes utan,
        hanem tenylegesen addig probalkozzon, amig a keresett UI elem meg nem
        jelenik (pl. betoltodik egy oldal), de legfeljebb timeout_seconds-ig.
        Konkret elemre varashoz (resource-id/osztaly alapjan is) hasznald a
        'wait_for_element' tool-t.
        """
        import asyncio
        import time

        deadline = time.monotonic() + max(1, min(60, timeout_seconds))

        while time.monotonic() < deadline:
            xml_text, real_serial = await fetch_ui_dump_xml(serial)
            if text.lower() in xml_text.lower():
                return f"Megtalalva: {text!r} megjelent a kepernyon."
            serial = real_serial
            await asyncio.sleep(1.0)

        return f"Idotullepes: {text!r} nem jelent meg {timeout_seconds} masodperc alatt."

    @mcp.tool()
    async def observe_screen(serial: SerialArg = None, include_screenshot: bool = False):
        """Egyetlen hivassal osszegyujti a kepernyo aktualis allapotat.

        Visszaadja egyben: eloterben lathato alkalmazas/aktivitas, kepernyomeret
        es -orientacio, es a fontosabb (kattinthato/szerkesztheto) UI-elemek
        listaja. Ezzel egy agentnek nem kell minden lepes elott 3-4 kulon
        tool-t hivnia (foreground_app + ui_dump + screen_state) - egy hivasbol
        latja az aktualis 'jelenetet'. include_screenshot=True eseten a
        kepernyokep is mellekelve van (kulon uzenetkent, mert a valasz maga
        szoveges marad).
        """
        real_serial = await resolve_serial(serial)

        foreground = await run_shell(
            "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' 2>/dev/null "
            "|| dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity'",
            serial=real_serial, timeout=15.0,
        )
        size_out = await run_shell("wm size", serial=real_serial)

        xml_text, _ = await fetch_ui_dump_xml(real_serial)
        elements = parse_ui_elements(xml_text)
        interactive = [e for e in elements if e["clickable"] or e["editable"]]

        lines = [
            f"Eloterben: {foreground.strip() or '(nem allapithato meg)'}",
            f"Kepernyo: {size_out.strip()}",
            f"UI elemek ({len(interactive)} interaktiv, {len(elements)} osszesen):",
        ]
        lines.extend(format_element(e) for e in interactive[:60])
        if len(interactive) > 60:
            lines.append(f"... es meg {len(interactive) - 60} tovabbi elem (hasznald a 'ui_dump'-ot a teljes listahoz)")

        text_result = truncate("\n".join(lines))
        audit("observe_screen", serial=real_serial, element_count=len(elements))

        if not include_screenshot:
            return text_result

        result = await run_adb(["exec-out", "screencap", "-p"], serial=real_serial,
                                timeout=20.0, binary=True)
        if result.returncode == 0:
            img = Image(data=result.stdout.encode("latin-1"), format="png")
            return [text_result, img]
        return text_result
