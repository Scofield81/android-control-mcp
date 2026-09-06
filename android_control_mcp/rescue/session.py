"""scrcpy alfolyamat-inditas: tukrozes es AOA/OTG mod.

Ez a modul NEM implementalja ujra a scrcpy video/vezerlo protokolljat -
egyszeruen elinditja a valodi, hivatalos scrcpy.exe-t a megfelelo
kapcsolokkal, sajat (natokivan felugro) ablakaban. Az MCP szerver csak a
folyamatot inditja/allitja le es kovet nyomon egy egyszeru registry-ben -
maga a video-dekodolas, ablakkezeles, eger/billentyuzet-tovabbitas mind a
scrcpy sajat, bevalt kodjaban tortenik.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from .scrcpy_binary import detect_scrcpy

# Streaming profilok: minosegi/latencia preset-ek, amiket a scrcpy sajat
# parancssori kapcsoloira forditunk. Nem allitunk konkret FPS/bitrate szamokat
# "mert jol hangzik" - ezek a scrcpy hivatalos ajanlott ertekei a celhoz.
PROFILES: dict[str, list[str]] = {
    "quality": ["--video-bit-rate=16M", "--max-size=0"],
    "balanced": ["--video-bit-rate=8M", "--max-size=1920"],
    "low_latency": ["--video-bit-rate=4M", "--max-size=1280", "--max-fps=30"],
    "gaming": ["--video-bit-rate=12M", "--max-size=1920", "--max-fps=60"],
}


@dataclass
class RescueSession:
    kind: str  # "mirror" | "otg"
    process: asyncio.subprocess.Process
    serial: str | None
    profile: str
    args: list[str] = field(default_factory=list)

    @property
    def pid(self) -> int:
        return self.process.pid

    def is_running(self) -> bool:
        return self.process.returncode is None


_active_sessions: dict[int, RescueSession] = {}


async def start_mirror_session(serial: str | None, profile: str = "balanced",
                                scrcpy_path: str | None = None) -> RescueSession:
    """Teljes kepernyo-tukrozes + vezerles inditasa (ADB-t igenyel, mar
    engedelyezett eszkozon). A scrcpy sajat ablakaban jelenik meg - resize,
    fullscreen, rotation, high-DPI mind a scrcpy sajat, bevalt kezelese."""
    info = await detect_scrcpy(explicit_path=scrcpy_path)
    if not info.available:
        raise RuntimeError(info.detail)

    if profile not in PROFILES:
        raise ValueError(f"Ismeretlen profil: {profile!r}. Ervenyes: {', '.join(PROFILES)}")

    args = [info.executable]
    if serial:
        args += ["-s", serial]
    args += PROFILES[profile]

    process = await asyncio.create_subprocess_exec(*args)
    session = RescueSession(kind="mirror", process=process, serial=serial, profile=profile, args=args)
    _active_sessions[process.pid] = session
    return session


async def start_otg_session(serial_hint: str | None = None,
                             scrcpy_path: str | None = None) -> RescueSession:
    """ADB-t NEM igenylo AOA/HID vezerles inditasa ('scrcpy --otg').

    FONTOS KORLAT (dokumentald a hivonak): --otg modban NINCS video es NINCS
    audio - a scrcpy a szamitogep SAJAT, fizikai billentyuzetet/eleret
    tovabbitja a telefonnak USB HID-kent. Ha a felhasznalo latja a telefon
    kijelzojet (csak az erintes/ujjlenyomat halott), az o sajat egeret/
    billentyuzetet hasznalva tud PIN-t/mintat beirni - ez NEM automatikus
    probalgatas, a felhasznalo tudja, mit ir be.
    """
    info = await detect_scrcpy(explicit_path=scrcpy_path)
    if not info.available:
        raise RuntimeError(info.detail)

    args = [info.executable, "--otg"]
    if serial_hint:
        args += ["-s", serial_hint]

    process = await asyncio.create_subprocess_exec(*args)
    session = RescueSession(kind="otg", process=process, serial=serial_hint, profile="otg", args=args)
    _active_sessions[process.pid] = session
    return session


def list_sessions() -> list[RescueSession]:
    """A nyilvantartott munkamenetek listaja - a mar leallt folyamatok is
    benne maradnak (is_running()==False-szal), amig valaki 'stop_session'-t
    nem hiv rajuk, hogy a hivo lassa, mi tortent velük."""
    return list(_active_sessions.values())


async def stop_session(pid: int) -> bool:
    session = _active_sessions.get(pid)
    if session is None:
        return False
    if session.is_running():
        session.process.terminate()
        try:
            await asyncio.wait_for(session.process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            session.process.kill()
    del _active_sessions[pid]
    return True
