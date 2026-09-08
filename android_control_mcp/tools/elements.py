"""Szemantikus UI-vezerles: kereses/koppintas/gepeles szoveg vagy resource-id
alapjan, koordinatak kezi szamolasa/hurcolasa nelkul.

Ez a legnagyobb hasznossag-ugras a nyers 'ui_dump -> tap(x,y)' folyamathoz
kepest: a modellnek nem kell kettevalasztania a "keresd meg" es "koppints ra"
lepeseket, es nem kell koordinata-parokat athurcolnia tool-hivasok kozott.
"""

from __future__ import annotations

import asyncio
import time

from ..config import Mode
from ..permissions import require_mode
from .common import (
    SerialArg,
    do_swipe,
    do_tap,
    do_type_text,
    fetch_ui_dump_xml,
    find_matching_elements,
    format_element,
    parse_ui_elements,
    sh_quote,
)


async def _resolve_target(serial: SerialArg, text: str, resource_id: str, class_name: str,
                           index: int) -> tuple[dict | None, str, list[dict]]:
    xml_text, real_serial = await fetch_ui_dump_xml(serial)
    elements = parse_ui_elements(xml_text)
    matches = find_matching_elements(elements, text=text, resource_id=resource_id, class_name=class_name)
    if not matches or index >= len(matches):
        return None, real_serial, matches
    return matches[index], real_serial, matches


def register(mcp) -> None:

    @mcp.tool()
    async def find_element(text: str = "", resource_id: str = "", class_name: str = "",
                            serial: SerialArg = None) -> str:
        """UI-elemek keresese szoveg/tartalom-leiras, resource-id es/vagy osztaly
        (reszleges, kis-nagybetu-fuggetlen) alapjan az aktualis kepernyon.

        Legalabb egy szurot adj meg. Tobb talalat eseten mindegyiket felsorolja
        'element_id'-vel egyutt - azt add at a 'tap_element'/'type_into'
        'index' parametereben, ha nem az elso (index=0) talalatot akarod.
        """
        if not (text or resource_id or class_name):
            return "Adj meg legalabb egy szurot: text, resource_id vagy class_name."

        xml_text, _real_serial = await fetch_ui_dump_xml(serial)
        elements = parse_ui_elements(xml_text)
        matches = find_matching_elements(elements, text=text, resource_id=resource_id, class_name=class_name)

        if not matches:
            return f"Nincs talalat (text={text!r}, resource_id={resource_id!r}, class_name={class_name!r})."
        lines = [f"{len(matches)} talalat:"]
        lines.extend(f"[index={i}] {format_element(m)}" for i, m in enumerate(matches))
        return "\n".join(lines)

    @mcp.tool()
    async def tap_element(text: str = "", resource_id: str = "", class_name: str = "",
                           index: int = 0, serial: SerialArg = None) -> str:
        """Koppintas egy UI-elemre szoveg/resource-id/osztaly alapjan (kereses+koppintas
        egyben - nem kell kulon 'find_element' + 'tap' koordinatakkal).

        Ha tobb elem is illik a szurore, 'index'-szel valaszthatod ki, melyikre
        (0 = elso talalat). Hiba eseten a talalatok listajat adja vissza, hogy
        lasd, mit erdemes pontositani.
        """
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        target, real_serial, matches = await _resolve_target(serial, text, resource_id, class_name, index)
        if target is None:
            if matches:
                lines = [f"Nincs 'index={index}' talalat, de van {len(matches)} egyeb:"]
                lines.extend(f"[index={i}] {format_element(m)}" for i, m in enumerate(matches))
                return "\n".join(lines)
            return f"Nincs talalat (text={text!r}, resource_id={resource_id!r}, class_name={class_name!r})."

        if target["center"] is None:
            return f"A talalt elemnek nincs ervenyes koordinataja: {format_element(target)}"

        cx, cy = target["center"]
        await do_tap(cx, cy, real_serial)
        return f"Koppintas: {format_element(target)}"

    @mcp.tool()
    async def type_into(text: str, field_text: str = "", resource_id: str = "",
                         class_name: str = "", index: int = 0, serial: SerialArg = None) -> str:
        """Szoveg beirasa egy adott mezobe: megkeresi, ra koppint (fokuszalja),
        majd beirja a szoveget - egy hivasban.

        'field_text'/'resource_id'/'class_name' azonositja a CELMEZOT (nem a
        beirando szoveget - az a 'text' parameter). Ha egyik szurot sem adod
        meg, az elso szerkesztheto (EditText) mezot celozza.
        """
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")

        xml_text, real_serial = await fetch_ui_dump_xml(serial)
        elements = parse_ui_elements(xml_text)

        if field_text or resource_id or class_name:
            matches = find_matching_elements(elements, text=field_text, resource_id=resource_id,
                                              class_name=class_name)
        else:
            matches = [e for e in elements if e["editable"]]

        if not matches or index >= len(matches):
            return (f"Nincs megfelelo celmezo (field_text={field_text!r}, resource_id={resource_id!r}). "
                    f"Hasznald a 'find_element'-et a lehetosegek attekintesehez.")

        target = matches[index]
        if target["center"] is None:
            return f"A celmezonek nincs ervenyes koordinataja: {format_element(target)}"

        cx, cy = target["center"]
        await do_tap(cx, cy, real_serial)
        await asyncio.sleep(0.2)  # fokuszvaltas/billentyuzet megjelenes rovid ideje

        if text.isascii():
            await do_type_text(text, real_serial)
            method = "input_text"
        else:
            from ..adb import run_shell
            await run_shell(f"cmd clipboard set-primary-clip text/plain {sh_quote(text)}",
                             serial=real_serial)
            await run_shell("input keyevent KEYCODE_PASTE", serial=real_serial)
            method = "clipboard_paste"

        return f"Beirva ({method}) ide: {format_element(target)}"

    @mcp.tool()
    async def scroll_to(text: str, max_swipes: int = 8, serial: SerialArg = None) -> str:
        """Lefele gorget, amig a keresett szoveg meg nem jelenik a kepernyon
        (vagy el nem eri a max_swipes limitet).

        Hasznos hosszu listakhoz/beallitas-oldalakhoz, ahol a keresett elem
        eleve nem is lathato meg a gorgetes elott.
        """
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        max_swipes = max(1, min(20, max_swipes))

        for attempt in range(max_swipes):
            xml_text, real_serial = await fetch_ui_dump_xml(serial)
            if text.lower() in xml_text.lower():
                elements = parse_ui_elements(xml_text)
                matches = find_matching_elements(elements, text=text)
                detail = f" ({format_element(matches[0])})" if matches else ""
                return f"Megtalalva {attempt} gorgetes utan: {text!r}{detail}"

            from ..adb import run_shell
            size_out = await run_shell("wm size", serial=real_serial)
            try:
                dims = size_out.strip().split(":")[-1].strip()
                w, h = (int(v) for v in dims.split("x"))
            except (ValueError, IndexError):
                w, h = 1080, 1920
            cx = w // 2
            await do_swipe(cx, int(h * 0.75), cx, int(h * 0.25), 300, real_serial)
            await asyncio.sleep(0.3)
            serial = real_serial

        return f"Nem talalhato '{text}' {max_swipes} gorgetes utan."

    @mcp.tool()
    async def wait_for_element(text: str = "", resource_id: str = "", timeout_seconds: int = 10,
                                serial: SerialArg = None) -> str:
        """Var, amig egy adott elem (szoveg es/vagy resource-id alapjan)
        megjelenik a kepernyon, legfeljebb timeout_seconds-ig.

        A 'wait_for_text' egyszeru substring-keresest vegez a nyers XML-ben;
        ez a tool a strukturalt elem-listaban keres, igy resource-id-re is
        tud varni (ami nem feltetlenul lathato szovegkent a kepernyon).
        """
        if not (text or resource_id):
            return "Adj meg legalabb egyet: text vagy resource_id."

        deadline = time.monotonic() + max(1, min(60, timeout_seconds))
        while time.monotonic() < deadline:
            xml_text, real_serial = await fetch_ui_dump_xml(serial)
            elements = parse_ui_elements(xml_text)
            matches = find_matching_elements(elements, text=text, resource_id=resource_id)
            if matches:
                return f"Megtalalva: {format_element(matches[0])}"
            serial = real_serial
            await asyncio.sleep(1.0)

        return f"Idotullepes: nincs talalat (text={text!r}, resource_id={resource_id!r}) {timeout_seconds}s alatt."
