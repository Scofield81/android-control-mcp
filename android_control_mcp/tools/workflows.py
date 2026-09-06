"""Magasabb szintu, tobb lepest osszevonoa 'workflow' tool-ok - meglevo
primitiv tool-okra epulve, hogy tipikus AI-tesztelesi/automatizalasi
mintakhoz ne kelljen 4-5 kulon hivast osszefuznie a hivo agentnek.
"""

from __future__ import annotations

import asyncio
import time

from ..adb import run_shell
from ..audit import audit
from ..config import Mode
from ..permissions import require_mode
from .common import (
    SerialArg,
    do_tap,
    do_type_text,
    fetch_ui_dump_xml,
    find_matching_elements,
    parse_ui_elements,
    resolve_serial,
    sh_quote,
    validate_package_name,
)


def register(mcp) -> None:

    @mcp.tool()
    async def open_app_and_wait(package: str, timeout_seconds: int = 10, serial: SerialArg = None) -> str:
        """Alkalmazas inditasa, es varakozas, amig tenylegesen az kerul elotterbe.

        Egy hivasban vegzi el, amit kulon 'launch_app' + tobbszori
        'foreground_app' ellenorzes tenne - hasznos, ha biztosra akarsz menni,
        hogy az app tenyleg elindult, mielott tovabbi lepeseket teszel.
        """
        require_mode(Mode.NORMAL, what="alkalmazas inditasa")
        package = validate_package_name(package)
        real_serial = await resolve_serial(serial)

        await run_shell(f"monkey -p {sh_quote(package)} -c android.intent.category.LAUNCHER 1",
                         serial=real_serial)

        deadline = time.monotonic() + max(1, min(30, timeout_seconds))
        while time.monotonic() < deadline:
            focus = await run_shell(
                "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' 2>/dev/null "
                "|| dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity'",
                serial=real_serial, timeout=15.0,
            )
            if package in focus:
                audit("open_app_and_wait", serial=real_serial, package=package, ok=True)
                return f"Elinditva es elotterben: {package}\n{focus.strip()}"
            await asyncio.sleep(0.5)

        audit("open_app_and_wait", serial=real_serial, package=package, ok=False)
        return (f"'{package}' inditasa elkuldve, de {timeout_seconds}s alatt nem lett igazoltan "
                "elotterben - ellenorizd 'foreground_app'-pal vagy 'screenshot'-tal.")

    @mcp.tool()
    async def fill_form(fields: dict, serial: SerialArg = None) -> str:
        """Tobb mezo kitoltese egy hivasban.

        'fields' kulcsa a celmezo resource-id-ja (lasd 'find_element'/'ui_dump'),
        erteke a beirando szoveg. Pl.: {"com.app:id/email": "pelda@pelda.hu",
        "com.app:id/password": "titok"}. Minden mezot sorban megkeres,
        rakoppint, majd beirja a szoveget (unicode-biztos modon).
        """
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        results = []
        for resource_id, value in fields.items():
            xml_text, real_serial = await fetch_ui_dump_xml(serial)
            elements = parse_ui_elements(xml_text)
            matches = find_matching_elements(elements, resource_id=resource_id)
            if not matches:
                results.append(f"✗ {resource_id}: nincs talalat")
                continue

            target = matches[0]
            if target["center"] is None:
                results.append(f"✗ {resource_id}: nincs ervenyes koordinata")
                continue

            cx, cy = target["center"]
            await do_tap(cx, cy, real_serial)
            await asyncio.sleep(0.2)
            if value.isascii():
                await do_type_text(value, real_serial)
            else:
                await run_shell(f"cmd clipboard set-primary-clip text/plain {sh_quote(value)}",
                                 serial=real_serial)
                await run_shell("input keyevent KEYCODE_PASTE", serial=real_serial)
            results.append(f"✓ {resource_id}: kitoltve")
            serial = real_serial

        audit("fill_form", field_count=len(fields))
        return "\n".join(results)

    @mcp.tool()
    async def wait_until_screen_changes(timeout_seconds: int = 10, serial: SerialArg = None) -> str:
        """Var, amig a kepernyo UI-tartalma erzekelhetoen valtozik (nem ugyanaz
        a UI-hierarchia, mint a hivaskori allapot).

        Hasznos gomb-koppintas UTAN, amikor nem tudod elore, milyen konkret
        szoveg fog megjelenni, csak azt, hogy 'tortenjen valami'.
        """
        xml_before, real_serial = await fetch_ui_dump_xml(serial)
        deadline = time.monotonic() + max(1, min(60, timeout_seconds))

        while time.monotonic() < deadline:
            await asyncio.sleep(0.5)
            xml_now, real_serial = await fetch_ui_dump_xml(real_serial)
            if xml_now != xml_before:
                return "A kepernyo valtozott."

        return f"A kepernyo nem valtozott erzekelhetoen {timeout_seconds} masodperc alatt."

    @mcp.tool()
    async def assert_text(text: str, should_exist: bool = True, serial: SerialArg = None) -> str:
        """Ellenorzi, hogy egy szoveg lathato-e (vagy NEM lathato-e) a kepernyon.

        Hasznos automatizalt tesztfolyamatok zaro lepeserekent ('sikeres'
        felirat megjelent-e, hibauzenet NEM jelent-e meg, stb.). Sose dob
        kivetelt - mindig egy vilagos PASS/FAIL szoveget ad vissza, hogy az
        agent eldonthesse, mit tegyen.
        """
        xml_text, _real_serial = await fetch_ui_dump_xml(serial)
        found = text.lower() in xml_text.lower()
        ok = found if should_exist else not found

        status = "PASS" if ok else "FAIL"
        expectation = "megjelenjen" if should_exist else "NE jelenjen meg"
        return f"{status}: '{text}' elvart, hogy {expectation} a kepernyon - ez {'igaz' if found else 'hamis'}."
