"""Bemeneti (gesztus + billentyuzet) tool-ok - 'input' es 'keyevent' ADB parancsokra epulve.

Az alap koppintas/gepeles-logika a common.py-ban van (do_tap/do_swipe/do_type_text),
hogy a kesobbi szemantikus tool-ok (tap_element, type_into - lasd elements.py)
ugyanazt a, mar bizonyitottan biztonsagos (idezett/validalt) kodot hasznaljak,
ne kulon-kulon ujraimplementalt valtozatokat.
"""

from __future__ import annotations

import asyncio

from ..adb import resolve_serial, run_shell
from ..audit import audit
from ..config import Mode
from ..permissions import require_mode
from .common import SerialArg, do_swipe, do_tap, do_type_text, sh_quote, validate_keycode

# A leggyakoribb Android keyevent-nevek, hogy az agentnek ne kelljen szamkodokat
# megjegyeznie. Barmilyen mas KEYCODE_* nev is mukodik, ez csak egy rovidites-tablazat.
_KEY_ALIASES = {
    "home": "KEYCODE_HOME", "back": "KEYCODE_BACK", "recents": "KEYCODE_APP_SWITCH",
    "power": "KEYCODE_POWER", "enter": "KEYCODE_ENTER", "tab": "KEYCODE_TAB",
    "delete": "KEYCODE_DEL", "backspace": "KEYCODE_DEL", "escape": "KEYCODE_ESCAPE",
    "volume_up": "KEYCODE_VOLUME_UP", "volume_down": "KEYCODE_VOLUME_DOWN",
    "volume_mute": "KEYCODE_VOLUME_MUTE", "camera": "KEYCODE_CAMERA",
    "menu": "KEYCODE_MENU", "search": "KEYCODE_SEARCH",
    "up": "KEYCODE_DPAD_UP", "down": "KEYCODE_DPAD_DOWN",
    "left": "KEYCODE_DPAD_LEFT", "right": "KEYCODE_DPAD_RIGHT",
    "play_pause": "KEYCODE_MEDIA_PLAY_PAUSE", "next": "KEYCODE_MEDIA_NEXT",
    "previous": "KEYCODE_MEDIA_PREVIOUS", "notification": "KEYCODE_NOTIFICATION",
    "paste": "KEYCODE_PASTE",
}


def register(mcp) -> None:

    @mcp.tool()
    async def tap(x: int, y: int, serial: SerialArg = None) -> str:
        """Koppintas a kepernyo (x, y) pixelkoordinatajan.

        A koordinatakat legjobb az 'ui_dump' tool 'center=' ertekebol venni,
        vagy meg jobban a 'tap_element' tool-t hasznalni koordinata-szamolas
        nelkul, ha van szoveg/resource-id, amire hivatkozni lehet.
        """
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        real_serial = await do_tap(x, y, serial)
        audit("tap", serial=real_serial, x=x, y=y)
        return f"Koppintas: ({x}, {y})"

    @mcp.tool()
    async def double_tap(x: int, y: int, serial: SerialArg = None) -> str:
        """Dupla koppintas (x, y)-on - pl. kep nagyitasahoz/kicsinyitesehez."""
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        real_serial = await do_tap(x, y, serial)
        await asyncio.sleep(0.1)
        await do_tap(x, y, real_serial)
        audit("double_tap", serial=real_serial, x=x, y=y)
        return f"Dupla koppintas: ({x}, {y})"

    @mcp.tool()
    async def long_press(x: int, y: int, duration_ms: int = 800, serial: SerialArg = None) -> str:
        """Hosszan tartott nyomas (x, y)-on - pl. kontextusmenuhoz vagy elem kijeloleshez."""
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        duration_ms = max(300, min(5000, duration_ms))
        real_serial = await do_swipe(x, y, x, y, duration_ms, serial)
        audit("long_press", serial=real_serial, x=x, y=y, duration_ms=duration_ms)
        return f"Hosszan tartott nyomas: ({x}, {y}), {duration_ms} ms"

    @mcp.tool()
    async def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300,
                     serial: SerialArg = None) -> str:
        """Csuszo mozdulat (x1,y1) -> (x2,y2) pontok kozott, duration_ms ideig."""
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        duration_ms = max(50, min(5000, duration_ms))
        real_serial = await do_swipe(x1, y1, x2, y2, duration_ms, serial)
        audit("swipe", serial=real_serial, x1=x1, y1=y1, x2=x2, y2=y2, duration_ms=duration_ms)
        return f"Swipe: ({x1},{y1}) -> ({x2},{y2}), {duration_ms} ms"

    @mcp.tool()
    async def drag(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 600,
                    serial: SerialArg = None) -> str:
        """Huzas (drag) (x1,y1)-tol (x2,y2)-ig - hosszabb ideju swipe, hogy az UI
        drag-nak, ne csak gyors flick-nek erzekelje (pl. listaelem atrendezese)."""
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        duration_ms = max(300, min(8000, duration_ms))
        real_serial = await do_swipe(x1, y1, x2, y2, duration_ms, serial)
        audit("drag", serial=real_serial, x1=x1, y1=y1, x2=x2, y2=y2, duration_ms=duration_ms)
        return f"Drag: ({x1},{y1}) -> ({x2},{y2}), {duration_ms} ms"

    @mcp.tool()
    async def scroll(direction: str, amount: int = 600, serial: SerialArg = None) -> str:
        """Gorgetes a kepernyo kozepetol: 'up', 'down', 'left' vagy 'right'.

        Ez csak egy kenyelmi wrapper a 'swipe' korul szemantikus iranyokkal -
        ha egy konkret szoveghez akarsz gorgetni, hasznald a 'scroll_to' tool-t.
        """
        direction = direction.lower().strip()
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        real_serial = await resolve_serial(serial)
        size_out = await run_shell("wm size", serial=real_serial)
        try:
            dims = size_out.strip().split(":")[-1].strip()
            w, h = (int(v) for v in dims.split("x"))
        except Exception:
            w, h = 1080, 1920
        cx, cy = w // 2, h // 2
        half = amount // 2

        vectors = {
            "up": (cx, cy + half, cx, cy - half),
            "down": (cx, cy - half, cx, cy + half),
            "left": (cx + half, cy, cx - half, cy),
            "right": (cx - half, cy, cx + half, cy),
        }
        if direction not in vectors:
            return f"Ervenytelen irany: {direction!r}. Hasznalj: up, down, left, right."

        x1, y1, x2, y2 = vectors[direction]
        await do_swipe(x1, y1, x2, y2, 300, real_serial)
        audit("scroll", serial=real_serial, direction=direction, amount=amount)
        return f"Gorgetes: {direction}"

    @mcp.tool()
    async def type_text(text: str, serial: SerialArg = None) -> str:
        """Szoveg begepelese az aktivan fokuszalt beviteli mezobe.

        Automatikusan valasztja a megfelelo modszert: tiszta ASCII szoveghez az
        'input text'-et hasznalja; ekezetes/unicode szoveg eseten (pl. magyar
        ekezetek) automatikusan a vagolap+beillesztes utat valasztja
        ('paste_clipboard' + KEYCODE_PASTE), ami megbizhatobb Android 10+-on -
        nem kell kulon 'paste_clipboard'-ot es hosszu nyomast hivnod kezzel.
        """
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")

        if text.isascii():
            real_serial = await do_type_text(text, serial)
            audit("type_text", serial=real_serial, length=len(text), method="input_text")
            return f"Szoveg beirva ({len(text)} karakter, ASCII input)."

        real_serial = await resolve_serial(serial)
        await run_shell(f"cmd clipboard set-primary-clip text/plain {sh_quote(text)}", serial=real_serial)
        paste_ok = True
        try:
            await run_shell("input keyevent KEYCODE_PASTE", serial=real_serial)
        except Exception:
            paste_ok = False
        audit("type_text", serial=real_serial, length=len(text), method="clipboard_paste")
        if paste_ok:
            return (
                f"Szoveg a vagolapra masolva es KEYCODE_PASTE-tel beillesztve ({len(text)} "
                "karakter, unicode/ekezetes ut). Ha a mezo nem tamogatja a hardveres beillesztes "
                "billentyut, hosszu nyomassal ('long_press' a mezon) es a megjeleno 'Beillesztes' "
                "gombra kattintva ('ui_dump' -> 'tap') is beilleszhetod."
            )
        return (
            f"Szoveg a vagolapra masolva ({len(text)} karakter), de a KEYCODE_PASTE nem "
            "mukodott ezen az eszkozon. Illeszd be kezzel: 'long_press' a mezon, majd a "
            "megjeleno 'Beillesztes' gombra 'tap' ('ui_dump' segit megtalalni)."
        )

    @mcp.tool()
    async def press_key(key: str, serial: SerialArg = None) -> str:
        """Hardver-/rendszerbillentyu lenyomasa.

        Rovidites-nevek: home, back, recents, power, enter, tab, delete, escape,
        volume_up, volume_down, volume_mute, up/down/left/right, menu, search,
        play_pause, next, previous, paste. Barmilyen mas 'KEYCODE_...' nev is
        mukodik kozvetlenul (lasd az Android KeyEvent dokumentaciojat) - a
        formatumot ellenorizzuk, mielott a shell parancsba kerulne.
        """
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        raw = _KEY_ALIASES.get(key.lower(), key if key.upper().startswith("KEYCODE_") else f"KEYCODE_{key.upper()}")
        code = validate_keycode(raw)
        real_serial = await resolve_serial(serial)
        await run_shell(f"input keyevent {sh_quote(code)}", serial=real_serial)
        audit("press_key", serial=real_serial, key=code)
        return f"Billentyu lenyomva: {code}"

    @mcp.tool()
    async def paste_clipboard(text: str, serial: SerialArg = None) -> str:
        """Szoveg masolasa az eszkoz vagolapjara ('cmd clipboard set-primary-clip').

        Ekezetes/unicode szoveghez altalaban egyszerubb kozvetlenul a
        'type_text'-et hasznalni - az automatikusan ezt az utat valasztja
        nem-ASCII szoveghez. Ezt a tool-t akkor erdemes kulon hivni, ha csak
        masolni akarsz (nem azonnal beilleszteni), vagy tobbszor akarod
        ugyanazt a szoveget beilleszteni.
        """
        require_mode(Mode.NORMAL, what="kepernyo-interakcio")
        real_serial = await resolve_serial(serial)
        await run_shell(f"cmd clipboard set-primary-clip text/plain {sh_quote(text)}", serial=real_serial)
        audit("paste_clipboard", serial=real_serial, length=len(text))
        return "Vagolapra masolva. Beillesztes: 'press_key(\"paste\")' vagy hosszu nyomas + 'Beillesztes'."
