"""Input-backend absztrakcio: ADB (mindig elerheto, alapertelmezett) vs.
opcionalis scrcpy-alapu gyors bemenet.

**KISERLETI / OPT-IN, NEM VALIDALVA VALODI ESZKOZON EBBEN A FEJLESZTESI
MENETBEN.** A tiszta `adb shell input` ut tipikusan ~100-300 ms/muvelet
(kulon `adb.exe` alfolyamat + USB korutazas minden koppintashoz). A
`scrcpy-client` csomag a scrcpy binaris vezerlo-protokolljat hasznalja egy
mar futo/perzisztens kapcsolaton keresztul, ami dokumentaltan ~5-10 ms-re
csokkentheti ezt (lasd README "Sebesseg" szakasz).

Ez a modul alapertelmezetten **KI VAN KAPCSOLVA** (`AdbInputBackend` fut
mindig) - csak akkor probal scrcpy-t hasznalni, ha explicit bekapcsoljak
(`ANDROID_CONTROL_SCRCPY=1`) ES a `scrcpy-client` csomag telepitve van ES a
kapcsolat tenylegesen sikerul. Barmilyen hiba eseten - importhiba, hianyzo
`av`/FFmpeg fuggoseg, sikertelen csatlakozas - csendben es VEGLEGESEN
(a folyamat eletciklusa alatt, az adott sorozatszamra) visszavalt ADB-re.
Soha nem dob kivetelt a hivo fele emiatt.
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional, Protocol


class InputBackend(Protocol):
    async def tap(self, x: int, y: int) -> None: ...
    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int) -> None: ...


class AdbInputBackend:
    """A mindig elerheto, mar bizonyitottan mukodo ADB-alapu ut."""

    def __init__(self, serial: str):
        self.serial = serial

    async def tap(self, x: int, y: int) -> None:
        from .adb import run_shell
        await run_shell(f"input tap {int(x)} {int(y)}", serial=self.serial)

    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int) -> None:
        from .adb import run_shell
        await run_shell(
            f"input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration_ms)}",
            serial=self.serial,
        )


class ScrcpyInputBackend:
    """Kiserleti, gyorsitott ut a 'scrcpy-client' csomagon keresztul.

    A csatlakozas lusta (elso hasznalatkor tortenik), es barmilyen hiba
    eseten `self._broken = True` allapotba kerul - ezutan minden hivas
    azonnal `RuntimeError`-t dob, amit a `get_backend()` cache-el es tobbet
    meg sem probal scrcpy-t hasznalni erre a sorozatszamra.
    """

    def __init__(self, serial: str):
        self.serial = serial
        self._client = None
        self._broken = False

    async def _ensure_client(self):
        if self._client is not None:
            return self._client
        if self._broken:
            raise RuntimeError("scrcpy backend korabban mar meghiusult ehhez az eszkozhoz")

        def _connect():
            import scrcpy  # opcionalis fuggoseg - csak itt probaljuk importalni

            client = scrcpy.Client(device=self.serial)
            client.start(threaded=True)
            return client

        try:
            self._client = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _connect), timeout=8.0
            )
        except Exception as exc:  # ImportError, kapcsolodasi hiba, timeout - mindegy melyik
            self._broken = True
            raise RuntimeError(f"scrcpy backend nem inicializalhato: {exc}") from exc

        return self._client

    async def tap(self, x: int, y: int) -> None:
        import scrcpy

        client = await self._ensure_client()
        client.control.touch(x, y, scrcpy.ACTION_DOWN)
        await asyncio.sleep(0.02)
        client.control.touch(x, y, scrcpy.ACTION_UP)

    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int) -> None:
        import scrcpy

        client = await self._ensure_client()
        steps = max(2, min(20, duration_ms // 30))
        client.control.touch(x1, y1, scrcpy.ACTION_DOWN)
        for i in range(1, steps + 1):
            ix = x1 + (x2 - x1) * i // steps
            iy = y1 + (y2 - y1) * i // steps
            client.control.touch(ix, iy, scrcpy.ACTION_MOVE)
            await asyncio.sleep(duration_ms / 1000 / steps)
        client.control.touch(x2, y2, scrcpy.ACTION_UP)


_backend_cache: dict[str, InputBackend] = {}
_scrcpy_globally_disabled = False


def scrcpy_requested() -> bool:
    return os.environ.get("ANDROID_CONTROL_SCRCPY", "").lower() in ("1", "true", "yes")


async def get_backend(serial: str) -> InputBackend:
    """A gyorsitott (scrcpy) vagy a biztos (ADB) backendet adja vissza egy
    adott eszkozhoz. Sose dob kivetelt - legrosszabb esetben is ADB-t ad."""
    global _scrcpy_globally_disabled

    if serial in _backend_cache:
        return _backend_cache[serial]

    if scrcpy_requested() and not _scrcpy_globally_disabled:
        candidate = ScrcpyInputBackend(serial)
        try:
            await candidate._ensure_client()
            _backend_cache[serial] = candidate
            return candidate
        except Exception:
            # Egy sikertelen probalkozas eleg - ne probalkozzunk ujra minden
            # egyes tap-nal, mert az maga is lassitana a (fallback) ADB utat.
            _scrcpy_globally_disabled = True

    backend = AdbInputBackend(serial)
    _backend_cache[serial] = backend
    return backend
