"""scrcpy alfolyamat-inditas: tukrozes es AOA/OTG mod.

Ez a modul NEM implementalja ujra a scrcpy video/vezerlo protokolljat -
egyszeruen elinditja a valodi, hivatalos scrcpy.exe-t a megfelelo
kapcsolokkal, sajat (natokivan felugro) ablakaban. Az MCP szerver csak a
folyamatot inditja/allitja le es kovet nyomon egy egyszeru registry-ben -
maga a video-dekodolas, ablakkezeles, eger/billentyuzet-tovabbitas mind a
scrcpy sajat, bevalt kodjaban tortenik.

Startup health-check: a scrcpy gyakran csak inditas UTAN, egy USB/driver/AOA
hiba miatt lep ki (pl. nincs jogosultsag, hianyzo driver, a telefon eppen
elutasitotta az AOA-kerest). Ha a folyamatot pusztan az elindulasatol sikeres
sessionkent kezelnenk, ez felrevezetne a hivot - ezert egy rovid varakozas
utan ellenorizzuk, hogy a folyamat tenyleg meg fut-e, es ha nem, a stderr
tartalmaval egyutt hibat dobunk induláskor sikertelennek.
"""

from __future__ import annotations

import asyncio
from collections import deque
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

_STARTUP_HEALTH_CHECK_DELAY = 1.0
"""Ennyit varunk inditas utan, mielott 'sikeresnek' konyveljuk el a sessiont.
Ha a scrcpy driver-/USB-/AOA-hiba miatt gyorsan kilep, ez az ido altalaban
eleg hozza - a valos ertek eszkozfuggo, ezt REAL DEVICE TEST-tel erdemes
finomhangolni."""

_STDERR_TAIL_LINES = 50


@dataclass
class RescueSession:
    kind: str  # "mirror" | "otg"
    process: asyncio.subprocess.Process
    serial: str | None
    profile: str
    args: list[str] = field(default_factory=list)
    stderr_tail: deque[str] = field(default_factory=lambda: deque(maxlen=_STDERR_TAIL_LINES))
    _pump_task: asyncio.Task | None = field(default=None, repr=False)

    @property
    def pid(self) -> int:
        return self.process.pid

    def is_running(self) -> bool:
        return self.process.returncode is None

    def stderr_text(self) -> str:
        return "\n".join(self.stderr_tail)


_active_sessions: dict[int, RescueSession] = {}


async def _pump_stderr(session: RescueSession) -> None:
    """Folyamatosan olvassa a scrcpy stderr-jet egy korlatozott meretu
    pufferbe - igy kesobb (akar egy kesobbi meghibasodaskor is) visszaadhato
    a legutobbi diagnosztikai kimenet, anelkul, hogy blokkolnank a folyamat
    kilepesere varva."""
    if session.process.stderr is None:
        return
    try:
        async for raw_line in session.process.stderr:
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            if line:
                session.stderr_tail.append(line)
    except Exception:
        pass  # a stream lezarasakor/folyamat kilepesekor termeszetes vege


def _prune_dead_sessions() -> None:
    """A mar nem futo, korabban meg nem takaritott sessionoket eltavolitja a
    nyilvantartasbol - opportunistikus takaritas minden uj session-inditaskor,
    hogy a registry ne nojon a vegtelensegig hosszu munkameneteknel."""
    for pid in [pid for pid, s in _active_sessions.items() if not s.is_running()]:
        del _active_sessions[pid]


async def _start_and_healthcheck(kind: str, args: list[str], serial: str | None,
                                  profile: str) -> RescueSession:
    _prune_dead_sessions()

    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE,
    )
    session = RescueSession(kind=kind, process=process, serial=serial, profile=profile, args=args)
    session._pump_task = asyncio.create_task(_pump_stderr(session))
    _active_sessions[process.pid] = session

    await asyncio.sleep(_STARTUP_HEALTH_CHECK_DELAY)

    if not session.is_running():
        # A folyamat mar kilepett a health-check-ablakon belul - ezt NEM
        # tekintjuk sikeres inditasnak. Eltavolitjuk a registry-bol es a
        # sszegyult stderr-rel egyutt hibat dobunk, hogy a hivo lassa, MIERT
        # lepett ki (pl. hianyzo driver, USB jogosultsag, AOA elutasitas).
        del _active_sessions[process.pid]
        stderr_text = session.stderr_text()
        detail = f" Hibauzenet:\n{stderr_text}" if stderr_text else " (nincs stderr-kimenet.)"
        raise RuntimeError(
            f"A scrcpy folyamat elindult, de {_STARTUP_HEALTH_CHECK_DELAY}s-en belul "
            f"kilepett (kilepesi kod: {process.returncode}).{detail}"
        )

    return session


async def start_mirror_session(serial: str | None, profile: str = "balanced",
                                scrcpy_path: str | None = None) -> RescueSession:
    """Teljes kepernyo-tukrozes + vezerles inditasa (ADB-t igenyel, mar
    engedelyezett eszkozon). A scrcpy sajat ablakaban jelenik meg - resize,
    fullscreen, rotation, high-DPI mind a scrcpy sajat, bevalt kezelese.

    Rovid startup health-check utan ter csak vissza (lasd modul-szintu
    dokumentacio) - igy egy azonnal meghiusulo inditas nem tunik hamisan
    sikeresnek."""
    info = await detect_scrcpy(explicit_path=scrcpy_path)
    if not info.available:
        raise RuntimeError(info.detail)

    if profile not in PROFILES:
        raise ValueError(f"Ismeretlen profil: {profile!r}. Ervenyes: {', '.join(PROFILES)}")

    args = [info.executable]
    if serial:
        args += ["-s", serial]
    args += PROFILES[profile]

    return await _start_and_healthcheck("mirror", args, serial, profile)


async def start_otg_session(serial_hint: str | None = None,
                             scrcpy_path: str | None = None) -> RescueSession:
    """ADB-t NEM igenylo AOA/HID vezerles inditasa ('scrcpy --otg').

    FONTOS KORLAT (dokumentald a hivonak): --otg modban NINCS video es NINCS
    audio - a scrcpy a szamitogep SAJAT, fizikai billentyuzetet/eleret
    tovabbitja a telefonnak USB HID-kent. Ha a felhasznalo latja a telefon
    kijelzojet (csak az erintes/ujjlenyomat halott), az o sajat egeret/
    billentyuzetet hasznalva tud PIN-t/mintat beirni - ez NEM automatikus
    probalgatas, a felhasznalo tudja, mit ir be.

    Rovid startup health-check utan ter csak vissza - lasd modul-szintu
    dokumentacio.
    """
    info = await detect_scrcpy(explicit_path=scrcpy_path)
    if not info.available:
        raise RuntimeError(info.detail)

    args = [info.executable, "--otg"]
    if serial_hint:
        args += ["-s", serial_hint]

    return await _start_and_healthcheck("otg", args, serial_hint, "otg")


def list_sessions() -> list[RescueSession]:
    """A jelenleg futo munkamenetek listaja. A mar leallt, de meg nem
    takaritott sessionok is szerepelhetnek benne (is_running()==False) - ezek
    a kovetkezo uj session-inditaskor automatikusan eltunnek a
    nyilvantartasbol (lasd _prune_dead_sessions)."""
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
    if session._pump_task is not None:
        session._pump_task.cancel()
    del _active_sessions[pid]
    return True
