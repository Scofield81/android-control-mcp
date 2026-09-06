"""Vekony wrapper az `adb` binaris korul.

Nincs kulon Python ADB-kliens-fuggoseg: minden hivas a rendszeren telepitett
`adb` (Android SDK Platform-Tools) parancssori eszkozt hivja meg
alfolyamatkent, ugyanugy, ahogy egy fejleszto is tenne a terminalban. Ez
tartja a fuggoseg-listat minimalisra, es garantalja, hogy amit ez a modul
csinal, azt egy ember is meg tudja ismetelni kezzel, debug celjabol.
"""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass

from .config import CONFIG


class AdbError(Exception):
    """Az adb parancs nem-nulla kilepesi koddal tert vissza, vagy nem talalhato."""


class NoDeviceError(AdbError):
    """Nincs eleg informacio ahhoz, hogy eldontsuk, melyik eszkozon fusson a parancs."""


@dataclass
class AdbResult:
    returncode: int
    stdout: str
    stderr: str


def adb_available() -> bool:
    return shutil.which(CONFIG.adb_path) is not None or CONFIG.adb_path not in ("adb",)


async def run_adb(
    args: list[str],
    *,
    serial: str | None = None,
    timeout: float = 30.0,
    binary: bool = False,
) -> AdbResult:
    """Egy `adb [-s SERIAL] <args...>` parancs futtatasa.

    binary=True eseten a stdout nyers bajtokent (latin-1-gyel dekodolva, hogy
    ne veszitsunk adatot) jon vissza - ez kell a `screencap`/`screenrecord`
    binaris kimenetehez.
    """
    cmd = [CONFIG.adb_path]
    if serial:
        cmd += ["-s", serial]
    cmd += args

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise AdbError(
            f"Az 'adb' parancs nem talalhato (probalt eleresi ut: {CONFIG.adb_path!r}). "
            "Telepitsd az Android SDK Platform-Tools csomagot, es ellenorizd, hogy az "
            "'adb' szerepel-e a PATH-ban, vagy allitsd be az ANDROID_CONTROL_ADB_PATH-t."
        ) from exc

    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.wait()
        raise AdbError(f"Az adb parancs tulleptte az idokorlatot ({timeout}s): {' '.join(args)}") from exc

    encoding = "latin-1" if binary else "utf-8"
    stdout = stdout_b.decode(encoding, errors="replace")
    stderr = stderr_b.decode("utf-8", errors="replace")

    return AdbResult(returncode=proc.returncode or 0, stdout=stdout, stderr=stderr)


async def run_adb_checked(args: list[str], *, serial: str | None = None,
                           timeout: float = 30.0, binary: bool = False) -> str:
    """Mint run_adb, de hibas kilepesi kod eseten AdbError-t dob a stderr-rel."""
    result = await run_adb(args, serial=serial, timeout=timeout, binary=binary)
    if result.returncode != 0:
        raise AdbError((result.stderr or result.stdout or "ismeretlen adb hiba").strip())
    return result.stdout


async def run_shell(command: str, *, serial: str | None = None, timeout: float = 30.0) -> str:
    """`adb shell <command>` - a leggyakrabban hasznalt muvelet."""
    return await run_adb_checked(["shell", command], serial=serial, timeout=timeout)


@dataclass
class DeviceEntry:
    serial: str
    state: str
    """pl. 'device', 'unauthorized', 'offline'"""


async def list_devices() -> list[DeviceEntry]:
    result = await run_adb(["devices"], timeout=10.0)
    entries: list[DeviceEntry] = []
    for line in result.stdout.splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            entries.append(DeviceEntry(serial=parts[0], state=parts[1]))
    return entries


async def resolve_serial(serial: str | None) -> str:
    """Eldonti, melyik eszkoz sorozatszamat hasznaljuk, ha a hivo nem adott meg egyet.

    Sorrend: explicit parameter -> CONFIG.default_serial -> az egyetlen
    csatlakoztatott, 'device' allapotu eszkoz. Ha tobb eszkoz van es nincs
    alapertelmezett, hibat dobunk - inkabb kerdezzunk vissza, mint hogy
    veletlenul a rossz telefonon hajtsunk vegre valamit.
    """
    if serial:
        return serial
    if CONFIG.default_serial:
        return CONFIG.default_serial

    devices = await list_devices()
    ready = [d for d in devices if d.state == "device"]
    unauthorized = [d for d in devices if d.state == "unauthorized"]

    if len(ready) == 1:
        return ready[0].serial
    if len(ready) == 0 and unauthorized:
        raise NoDeviceError(
            "Van csatlakoztatott eszkoz, de nincs jovahagyva ('unauthorized'). A telefonon "
            "jelenj meg egy 'USB hibakereses engedelyezese?' parbeszedablaknak - azt kell "
            "'Engedelyezem'-mel jovahagyni a telefon kepernyojen. Ha a kepernyo torott/nem "
            "hasznalhato, ez sajnos nem megkerulheto: ez az Android biztonsagi modellje, "
            "es ez a szoftver szandekosan nem probalja megkerulni."
        )
    if len(ready) == 0:
        raise NoDeviceError(
            "Nincs csatlakoztatott es engedelyezett Android eszkoz. Ellenorizd az USB-kabelt "
            "(vagy 'adb connect' vezetek nelkuli hibakereseshez), es hogy a telefonon be "
            "van-e kapcsolva a Fejlesztoi beallitasok > USB hibakereses."
        )
    raise NoDeviceError(
        f"Tobb csatlakoztatott eszkoz van ({', '.join(d.serial for d in ready)}), es nincs "
        "alapertelmezett megadva. Add meg a 'serial' parametert, vagy allitsd be az "
        "ANDROID_CONTROL_DEFAULT_SERIAL kornyezeti valtozot / 'default_serial'-t a configban."
    )
