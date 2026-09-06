"""Kozos segedletek a tool-modulok szamara."""

from __future__ import annotations

import re
import shlex
from typing import Optional

from ..adb import AdbError, NoDeviceError, resolve_serial, run_shell
from ..config import CONFIG, Mode
from ..permissions import PermissionDenied, require_mode

SerialArg = Optional[str]
"""Minden tool ugyanazt a 'serial' parametert fogadja: melyik eszkozon fusson.
None eseten a resolve_serial() donti el (config/alapertelmezett/egyetlen eszkoz)."""


def sh_quote(value: str) -> str:
    """Egyetlen shell-argumentum biztonsagos idezese, mielott egy `adb shell`
    parancssorba interpolalnank. MINDIG hasznald, ha felhasznaloi/hivo altal
    megadott ertek (fajlnev, csomagnev, URL, stb.) kerul bele egy shell-stringbe -
    kulonben shell injection lehetseges (pl. 'foo; rm -rf /sdcard' mint utvonal).

    A `shell_run` tool ez alol szandekosan kivetel: az kifejezetten tetszoleges
    parancs futtatasara szolgal, ADMIN modban es kockazat-megerositessel.
    """
    return shlex.quote(value)


_KEYCODE_RE = re.compile(r"^KEYCODE_[A-Z0-9_]+$")


def validate_keycode(code: str) -> str:
    """Egy 'input keyevent' celkod formai ellenorzese - csak 'KEYCODE_...' minta
    engedett, minden mas (pl. befuzott shell-metakarakter) elutasitva."""
    if not _KEYCODE_RE.match(code):
        raise ValueError(f"Ervenytelen keyevent kod: {code!r}. Formatum: 'KEYCODE_NEV'.")
    return code


async def do_tap(x: int, y: int, serial: SerialArg) -> str:
    real_serial = await resolve_serial(serial)
    from ..backends import scrcpy_requested

    if scrcpy_requested():
        from ..backends import get_backend
        backend = await get_backend(real_serial)
        await backend.tap(x, y)
    else:
        await run_shell(f"input tap {int(x)} {int(y)}", serial=real_serial)
    return real_serial


async def do_swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int, serial: SerialArg) -> str:
    real_serial = await resolve_serial(serial)
    from ..backends import scrcpy_requested

    if scrcpy_requested():
        from ..backends import get_backend
        backend = await get_backend(real_serial)
        await backend.swipe(x1, y1, x2, y2, duration_ms)
    else:
        await run_shell(
            f"input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration_ms)}",
            serial=real_serial,
        )
    return real_serial


def escape_input_text(text: str) -> str:
    """`input text` a szokozt kulon argumentumhatarnak veszi - ezert '%s'-re
    cserejuk, MIELOTT shlex.quote-tal egyetlen shell-argumentumma zarjuk."""
    return text.replace(" ", "%s")


async def do_type_text(text: str, serial: SerialArg) -> str:
    real_serial = await resolve_serial(serial)
    quoted = sh_quote(escape_input_text(text))
    await run_shell(f"input text {quoted}", serial=real_serial)
    return real_serial


_PACKAGE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+$")


def validate_package_name(package: str) -> str:
    """Android csomagnev (pl. 'com.example.app') formai ellenorzese.

    Nem csak idezi, hanem VISSZAUTASITJA az ervenytelen bemenetet - igy egy
    'com.foo; rm -rf /sdcard' tipusu probalkozas soha nem is jut el a shell
    parancs osszeallitasaig, nem csak escape-elve fut le hatastalanul.
    """
    if not _PACKAGE_RE.match(package):
        raise ValueError(
            f"Ervenytelen csomagnev: {package!r}. Egy Android csomagnev csak betuket, "
            "szamokat, alaphuzast es pontot tartalmazhat (pl. 'com.example.app')."
        )
    return package


async def dumpsys(section: str, *, serial: SerialArg = None, timeout: float = 15.0) -> str:
    real_serial = await resolve_serial(serial)
    return await run_shell(f"dumpsys {section}", serial=real_serial, timeout=timeout)


_UI_DUMP_REMOTE_PATH = "/sdcard/android_control_mcp_dump.xml"


async def fetch_ui_dump_xml(serial: SerialArg) -> tuple[str, str]:
    """Lekeri a jelenlegi kepernyo uiautomator XML dumpjat. Visszaadja az
    (xml_szoveg, real_serial) part - ezt hasznalja mind az 'ui_dump' tool
    (szoveges megjelenites), mind a szemantikus elemkereso tool-ok."""
    from ..adb import run_adb_checked  # kesoi import a korkoros import elkerulesere

    real_serial = await resolve_serial(serial)
    await run_adb_checked(["shell", f"uiautomator dump {_UI_DUMP_REMOTE_PATH}"],
                           serial=real_serial, timeout=20.0)
    xml_text = await run_adb_checked(["exec-out", "cat", _UI_DUMP_REMOTE_PATH],
                                      serial=real_serial, timeout=15.0)
    await run_shell(f"rm -f {_UI_DUMP_REMOTE_PATH}", serial=real_serial)
    return xml_text, real_serial


def parse_ui_elements(xml_text: str) -> list[dict]:
    """Az uiautomator XML dumpjat strukturalt elem-listava alakitja.

    Minden elem: id (sorszam ebben a dumpban), text, resource_id, class,
    clickable, enabled, selected, bounds ([x1,y1,x2,y2]), center ([cx,cy]).
    Csak azokat az elemeket adja vissza, amiknek van szovege/leirasa/resource-id-ja
    VAGY interaktivak - a teljesen dekorativ/ures elemek zajt jelentenenek.
    """
    import re as _re
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    bounds_re = _re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
    elements: list[dict] = []

    for idx, node in enumerate(root.iter("node")):
        text = node.get("text", "")
        desc = node.get("content-desc", "")
        res_id = node.get("resource-id", "")
        cls = node.get("class", "")
        clickable = node.get("clickable") == "true"
        enabled = node.get("enabled") == "true"
        selected = node.get("selected") == "true"
        editable = "EditText" in cls
        bounds_str = node.get("bounds", "")

        if not (text or desc or res_id or clickable or editable):
            continue

        m = bounds_re.match(bounds_str)
        bounds = None
        center = None
        if m:
            x1, y1, x2, y2 = map(int, m.groups())
            bounds = [x1, y1, x2, y2]
            center = [(x1 + x2) // 2, (y1 + y2) // 2]

        elements.append({
            "id": idx,
            "text": text,
            "content_desc": desc,
            "resource_id": res_id,
            "class": cls.rsplit(".", 1)[-1],
            "clickable": clickable,
            "editable": editable,
            "enabled": enabled,
            "selected": selected,
            "bounds": bounds,
            "center": center,
        })

    return elements


def find_matching_elements(elements: list[dict], *, text: str = "", resource_id: str = "",
                            class_name: str = "", exact: bool = False) -> list[dict]:
    """Elemek szurese szoveg/resource-id/osztaly alapjan (reszleges egyezes,
    kis-nagybetu-fuggetlen, hacsak exact=True nincs megadva)."""
    def _match(value: str, needle: str) -> bool:
        if not needle:
            return True
        if exact:
            return value == needle
        return needle.lower() in value.lower()

    results = []
    for el in elements:
        haystacks = [el["text"], el["content_desc"]]
        text_ok = not text or any(_match(h, text) for h in haystacks)
        resid_ok = _match(el["resource_id"], resource_id)
        class_ok = _match(el["class"], class_name)
        if text_ok and resid_ok and class_ok:
            results.append(el)
    return results


def format_element(el: dict) -> str:
    flags = "".join([
        "C" if el["clickable"] else "-",
        "T" if el["editable"] else "-",
        "E" if el["enabled"] else "-",
        "S" if el["selected"] else "-",
    ])
    label = el["text"] or el["content_desc"] or el["resource_id"].rsplit("/", 1)[-1] or "(nevtelen)"
    center = f"center={tuple(el['center'])}" if el["center"] else "center=?"
    return (f"#{el['id']} [{flags}] {el['class']} \"{label}\" "
            f"id={el['resource_id'] or '-'} {center}")


def format_error(exc: Exception) -> str:
    if isinstance(exc, (AdbError, NoDeviceError, PermissionDenied)):
        return str(exc)
    return f"Varatlan hiba: {exc}"
