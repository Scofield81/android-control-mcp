"""Kozos segedletek a tool-modulok szamara."""

from __future__ import annotations

from typing import Optional

from ..adb import AdbError, NoDeviceError, resolve_serial, run_shell
from ..config import CONFIG, Mode
from ..permissions import PermissionDenied, require_mode

SerialArg = Optional[str]
"""Minden tool ugyanazt a 'serial' parametert fogadja: melyik eszkozon fusson.
None eseten a resolve_serial() donti el (config/alapertelmezett/egyetlen eszkoz)."""


async def dumpsys(section: str, *, serial: SerialArg = None, timeout: float = 15.0) -> str:
    real_serial = await resolve_serial(serial)
    return await run_shell(f"dumpsys {section}", serial=real_serial, timeout=timeout)


def format_error(exc: Exception) -> str:
    if isinstance(exc, (AdbError, NoDeviceError, PermissionDenied)):
        return str(exc)
    return f"Varatlan hiba: {exc}"
