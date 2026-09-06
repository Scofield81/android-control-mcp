"""Rendszer-kapcsolok (wifi/bluetooth/repulo uzemmod/hangero) es kontextus-lekerdezes.

Ezek nelkul minden 'kapcsold be a repulo uzemmodot'-szeru keres csak UI-kattintasokkal
lett volna megoldhato (nyisd meg a Beallitasokat, keresd meg a kapcsolot, koppints ra) -
ezek egy-egy kozvetlen ADB paranccsal ugyanazt elerik, gyorsabban es megbizhatobban.
"""

from __future__ import annotations

from ..adb import resolve_serial, run_shell
from ..audit import audit
from ..config import Mode
from ..permissions import require_mode
from .common import SerialArg


def register(mcp) -> None:

    @mcp.tool()
    async def foreground_app(serial: SerialArg = None) -> str:
        """Az eppen elterben lathato alkalmazas es aktivitas neve.

        Ez adja a modellnek a 'kontextust' - mit lat most a felhasznalo a
        kepernyon - meg mielott ui_dump-ot vagy screenshot-ot kerne.
        """
        real_serial = await resolve_serial(serial)
        out = await run_shell(
            "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' 2>/dev/null "
            "|| dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity'",
            serial=real_serial, timeout=15.0,
        )
        return out.strip() or "Nem allapithato meg (probald az ui_dump-ot)."

    @mcp.tool()
    async def wifi_toggle(enabled: bool, serial: SerialArg = None) -> str:
        """Wifi be- vagy kikapcsolasa."""
        require_mode(Mode.NORMAL, what="wifi kapcsolasa")
        real_serial = await resolve_serial(serial)
        await run_shell(f"svc wifi {'enable' if enabled else 'disable'}", serial=real_serial)
        audit("wifi_toggle", serial=real_serial, enabled=enabled)
        return f"Wifi: {'BE' if enabled else 'KI'}"

    @mcp.tool()
    async def bluetooth_toggle(enabled: bool, serial: SerialArg = None) -> str:
        """Bluetooth be- vagy kikapcsolasa."""
        require_mode(Mode.NORMAL, what="bluetooth kapcsolasa")
        real_serial = await resolve_serial(serial)
        await run_shell(f"svc bluetooth {'enable' if enabled else 'disable'}", serial=real_serial)
        audit("bluetooth_toggle", serial=real_serial, enabled=enabled)
        return f"Bluetooth: {'BE' if enabled else 'KI'}"

    @mcp.tool()
    async def airplane_mode_toggle(enabled: bool, serial: SerialArg = None) -> str:
        """Repulo uzemmod be- vagy kikapcsolasa."""
        require_mode(Mode.NORMAL, what="repulo uzemmod kapcsolasa")
        real_serial = await resolve_serial(serial)
        value = "1" if enabled else "0"
        await run_shell(f"settings put global airplane_mode_on {value}", serial=real_serial)
        await run_shell(
            f"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state {str(enabled).lower()}",
            serial=real_serial,
        )
        audit("airplane_mode_toggle", serial=real_serial, enabled=enabled)
        return f"Repulo uzemmod: {'BE' if enabled else 'KI'}"

    @mcp.tool()
    async def set_volume(level: int, stream: str = "music", serial: SerialArg = None) -> str:
        """Hangero beallitasa. stream: 'music', 'ring', 'alarm', 'notification', 'call'.

        level: 0-tol a stream maximumaig (tipikusan 0-15, eszkoztol fuggoen).
        """
        require_mode(Mode.NORMAL, what="hangero allitasa")
        stream_ids = {"music": 3, "ring": 2, "alarm": 4, "notification": 5, "call": 0}
        stream_id = stream_ids.get(stream.lower(), 3)
        real_serial = await resolve_serial(serial)
        await run_shell(f"media volume --stream {stream_id} --set {int(level)}", serial=real_serial)
        audit("set_volume", serial=real_serial, stream=stream, level=level)
        return f"Hangero ({stream}): {level}"

    @mcp.tool()
    async def open_notification_panel(serial: SerialArg = None) -> str:
        """Az ertesitesi/gyorsbeallitasok panel lehuzasa a kepernyo tetejerol."""
        require_mode(Mode.NORMAL, what="ertesitesi panel megnyitasa")
        real_serial = await resolve_serial(serial)
        await run_shell("cmd statusbar expand-notifications", serial=real_serial)
        audit("open_notification_panel", serial=real_serial)
        return "Ertesitesi panel megnyitva."

    @mcp.tool()
    async def screen_orientation(rotation: str = "auto", serial: SerialArg = None) -> str:
        """Kepernyo-forgatas: 'auto', 'portrait', 'landscape', 'landscape_reverse'."""
        require_mode(Mode.NORMAL, what="kepernyo-forgatas allitasa")
        real_serial = await resolve_serial(serial)
        rotation = rotation.lower()
        if rotation == "auto":
            await run_shell("settings put system accelerometer_rotation 1", serial=real_serial)
            return "Automatikus forgatas: BE"

        codes = {"portrait": 0, "landscape": 1, "landscape_reverse": 3, "portrait_reverse": 2}
        if rotation not in codes:
            return "Ervenytelen ertek. Hasznalj: auto, portrait, landscape, landscape_reverse, portrait_reverse."
        await run_shell("settings put system accelerometer_rotation 0", serial=real_serial)
        await run_shell(f"settings put system user_rotation {codes[rotation]}", serial=real_serial)
        audit("screen_orientation", serial=real_serial, rotation=rotation)
        return f"Kepernyo-forgatas rogzitve: {rotation}"
