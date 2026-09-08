"""A hivatalos Genymobile/scrcpy binaris felismerese es kepesseg-ellenorzese.

Szandekosan NEM a PyPI 'scrcpy-client' csomagot hasznaljuk (az egy 2022-ben
elhagyott, scrcpy-server 1.20 protokollra epulo, Python <3.11-re korlatozott,
ujraimplementalt kliens - lasd docs/usage/RESCUE.md), hanem a rendszeren telepitett,
aktivan karbantartott scrcpy.exe/scrcpy binarist hivjuk alfolyamatkent -
pontosan ugy, ahogy egy fejleszto is tenne a terminalban. Igy semmilyen
protokoll-reszlet nincs nalunk ujraimplementalva, es a scrcpy sajat
verziofrissitesei automatikusan velunk maradnak kompatibilisek.
"""

from __future__ import annotations

import asyncio
import glob
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScrcpyInfo:
    executable: str
    version: str | None
    available: bool
    detail: str


def _candidate_paths() -> list[str]:
    """Tipikus telepitesi helyek Windows/macOS/Linux alatt, PATH-on kivul is -
    a scrcpy gyakran egy sima ZIP-bol kicsomagolt mappaban van, nem PATH-ban."""
    candidates = []
    local_appdata = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    if local_appdata:
        candidates.append(str(Path(local_appdata) / "scrcpy" / "scrcpy.exe"))
        # winget install Genymobile.scrcpy - a csomag valtozo hash-u/verzioju
        # almappaba csomagolja ki (pl. "...WinGet\Packages\Genymobile.scrcpy_
        # Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.1\scrcpy.exe"),
        # ezert glob-mintaval keressuk, nem fix utvonallal.
        winget_pattern = str(
            Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
            / "Genymobile.scrcpy_*" / "scrcpy-win64-v*" / "scrcpy.exe"
        )
        candidates += sorted(glob.glob(winget_pattern), reverse=True)
    if program_files:
        candidates.append(str(Path(program_files) / "scrcpy" / "scrcpy.exe"))
    candidates += [
        "/usr/bin/scrcpy",
        "/usr/local/bin/scrcpy",
        "/opt/homebrew/bin/scrcpy",
    ]
    return candidates


async def detect_scrcpy(explicit_path: str | None = None) -> ScrcpyInfo:
    """Megkeresi a scrcpy binarist es lekerdezi a verziojat.

    Sorrend: explicit_path (fuggveny-parameter) -> ANDROID_CONTROL_SCRCPY_PATH
    (kornyezeti valtozo) -> PATH -> tipikus telepitesi helyek (winget-tel
    telepitett scrcpy is ide tartozik). Soha nem dob kivetelt - hianyzo/hibas
    binaris eseten `available=False` es egy ember szamara ertheto `detail`
    uzenet jon vissza.

    JAVITAS (2026-09-06, valos eszkoz/valos scrcpy-telepitessel derult ki):
    korabban a hibauzenet az ANDROID_CONTROL_SCRCPY_PATH kornyezeti valtozot
    ajanlotta megoldaskent, de a kod ezt SOSEM olvasta ki - a valtozo
    beallitasa semmit nem valtoztatott volna, a scrcpy_path tool-parameter
    pedig meg csak nehany tool-on letezett (rescue_start_mirror/otg-n nem).
    """
    paths_to_try: list[str] = []
    if explicit_path:
        paths_to_try.append(explicit_path)

    env_path = os.environ.get("ANDROID_CONTROL_SCRCPY_PATH")
    if env_path:
        paths_to_try.append(env_path)

    which_result = shutil.which("scrcpy")
    if which_result:
        paths_to_try.append(which_result)

    paths_to_try += _candidate_paths()

    for path in paths_to_try:
        if path != "scrcpy" and not Path(path).is_file():
            continue
        version = await _try_get_version(path)
        if version is not None:
            return ScrcpyInfo(executable=path, version=version, available=True,
                               detail=f"scrcpy megtalalva: {path} (verzio: {version})")

    return ScrcpyInfo(
        executable="",
        version=None,
        available=False,
        detail=(
            "A hivatalos scrcpy nem talalhato. Toltsd le: "
            "https://github.com/Genymobile/scrcpy/releases (Windows: csomagold ki egy "
            "mappaba, es vagy add hozza a PATH-hoz, vagy add meg az "
            "ANDROID_CONTROL_SCRCPY_PATH kornyezeti valtozoval a scrcpy.exe teljes utvonalat)."
        ),
    )


async def _try_get_version(executable: str) -> str | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            executable, "--version",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
    except (FileNotFoundError, OSError, asyncio.TimeoutError):
        return None
    if proc.returncode != 0:
        return None
    first_line = stdout_b.decode("utf-8", errors="replace").splitlines()[0] if stdout_b else ""
    return first_line.strip() or "ismeretlen verzio"
