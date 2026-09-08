"""'android-control-mcp doctor' - PC-oldali diagnosztika.

Cel: egy pillantasra/egy JSON-hivassal eldontheto legyen, hogy a szerver
futtatasi kornyezete rendben van-e (Python, ADB, scrcpy, config, MCP
tool-regisztracio) - kulonosen fontos AI-agenteknek, akik a telepitest
maguk validaljak. SOSEM modosit Android-eszkozt: csak a PC-oldali
allapotot olvassa.

Hianyzo telefon/eszkoz NEM hiba (a szerver telefon nelkul is telepitheto/
inditható) - ezert egy csatlakoztatott eszkoz hianya sose 'error' szintu
allapotot ad, csak informativ 'NO DEVICE CONNECTED' sort.
"""

from __future__ import annotations

import asyncio
import json
import platform
import shutil
import sys
from dataclasses import dataclass, field

from . import __version__
from .adb import AdbError, list_devices
from .config import CONFIG


@dataclass
class CheckResult:
    name: str
    status: str  # "ok" | "warn" | "error" | "info"
    detail: str


@dataclass
class DoctorReport:
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, name: str, status: str, detail: str) -> None:
        self.checks.append(CheckResult(name, status, detail))

    @property
    def overall(self) -> str:
        if any(c.status == "error" for c in self.checks):
            return "NOT READY"
        if any(c.status == "warn" for c in self.checks):
            return "READY (figyelmeztetesekkel)"
        return "READY"

    def to_dict(self) -> dict:
        return {
            "overall": self.overall,
            "checks": [
                {"name": c.name, "status": c.status, "detail": c.detail} for c in self.checks
            ],
        }


async def _check_adb() -> tuple[str, str, str | None]:
    """(status, detail, adb_path)."""
    adb_path = shutil.which(CONFIG.adb_path) or CONFIG.adb_path
    if not shutil.which(CONFIG.adb_path) and CONFIG.adb_path == "adb":
        msg = (
            "Az 'adb' nem talalhato a PATH-on. Telepitsd az Android SDK "
            "Platform-Tools csomagot, vagy allitsd be az ANDROID_CONTROL_ADB_PATH-ot."
        )
        return "error", msg, None
    try:
        proc = await asyncio.create_subprocess_exec(
            adb_path, "version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
        if proc.returncode != 0:
            return "error", f"'{adb_path} version' hibaval tert vissza.", adb_path
        first_line = stdout_b.decode("utf-8", errors="replace").splitlines()[0]
        return "ok", first_line.strip(), adb_path
    except (FileNotFoundError, OSError, asyncio.TimeoutError) as exc:
        return "error", f"ADB nem futtathato: {exc}", adb_path


async def _check_scrcpy() -> tuple[str, str]:
    from .rescue.scrcpy_binary import detect_scrcpy

    info = await detect_scrcpy()
    if info.available:
        return "ok", info.detail
    return "warn", info.detail + " (a Rescue mod tukrozeshez szukseges, de a tobbi funkciot nem befolyasolja)"


def _check_python() -> tuple[str, str]:
    version = sys.version.split()[0]
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 10):
        return "error", f"Python {version} - a projekt Python 3.10+ -t igenyel."
    return "ok", f"Python {version}"


def _check_mcp_server() -> tuple[str, str, int]:
    try:
        from .server import mcp
        tools = mcp._tool_manager._tools  # type: ignore[attr-defined]
        count = len(tools)
        return "ok", f"MCP szerver betoltheto, {count} tool regisztralva.", count
    except (ImportError, AttributeError) as exc:
        return "error", f"MCP szerver betoltese sikertelen: {exc}", 0


async def _check_devices() -> tuple[str, str]:
    try:
        devices = await list_devices()
    except AdbError as exc:
        return "warn", f"'adb devices' lekerdezes sikertelen: {exc}"
    if not devices:
        return "info", "NO DEVICE CONNECTED (ez nem hiba - a telepites ettol meg rendben lehet)"
    lines = []
    for d in devices:
        # Wi-Fi ADB ket alakban jelenhet meg: "ip:port" VAGY mDNS-szolgaltatasnev
        # (pl. "adb-xxxxxxxx._adb-tls-connect._tcp") - egyik sem USB-soros-szam.
        # Csak akkor jelezzuk USB-nek, ha EGYIK Wi-Fi-mintara sem hasonlit -
        # igy sose cimkezunk tevesen egy Wi-Fi-kapcsolatot USB-nek.
        is_wifi = ":" in d.serial or "._tcp" in d.serial or d.serial.startswith("adb-")
        conn = "Wi-Fi ADB" if is_wifi else "USB ADB (feltehetoen - nem ip:port/mDNS alaku szerial)"
        lines.append(f"{d.serial} [{d.state}] ({conn})")
    status = "ok" if any(d.state == "device" for d in devices) else "warn"
    return status, "; ".join(lines)


def _check_config() -> tuple[str, str]:
    path = CONFIG.config_path
    if path.exists():
        return "ok", f"Config fajl: {path}"
    return "info", f"Nincs config fajl ezen az uton ({path}) - alapertelmezesek/kornyezeti valtozok ervenyesek."


async def run_doctor() -> DoctorReport:
    report = DoctorReport()

    report.add("OS", "ok", f"{platform.system()} {platform.release()} ({platform.version()})")

    py_status, py_detail = _check_python()
    report.add("Python", py_status, py_detail)

    report.add("Android Control MCP", "ok", f"verzio {__version__}")

    adb_status, adb_detail, _adb_path = await _check_adb()
    report.add("ADB", adb_status, adb_detail)

    scrcpy_status, scrcpy_detail = await _check_scrcpy()
    report.add("scrcpy", scrcpy_status, scrcpy_detail)

    cfg_status, cfg_detail = _check_config()
    report.add("Config", cfg_status, cfg_detail)

    mcp_status, mcp_detail, tool_count = _check_mcp_server()
    report.add("MCP server", mcp_status, mcp_detail)
    report.add("Tools", "ok" if tool_count else "error", str(tool_count))

    dev_status, dev_detail = await _check_devices()
    report.add("Devices", dev_status, dev_detail)

    if adb_status == "ok" and dev_status == "ok":
        report.add("Rescue capability", "info",
                    "Csatlakoztatott, engedelyezett eszkozzel a 'device_capabilities' tool "
                    "adja a reszletes kepesseg-jelentest (usb_host, aoa_hid, wired_video_output "
                    "stb.) - ez a doctor NEM ismetli meg, hogy ne legyen felreveto duplikatum.")
    else:
        report.add("Rescue capability", "info",
                    "Csatlakoztatott/engedelyezett eszkoz nelkul a Rescue kepessegek "
                    "'unknown' maradnak, amig egy eszkoz nincs csatlakoztatva.")

    return report


def render_human(report: DoctorReport) -> str:
    lines = ["Android Control MCP Doctor", ""]
    marker = {"ok": "OK", "warn": "WARN", "error": "ERROR", "info": "-"}
    for c in report.checks:
        dots = "." * max(1, 24 - len(c.name))
        lines.append(f"{c.name} {dots} {c.detail}  [{marker.get(c.status, c.status.upper())}]")
    lines += ["", f"Overall ................. {report.overall}"]
    return "\n".join(lines)


def main_doctor(as_json: bool) -> int:
    report = asyncio.run(run_doctor())
    if as_json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_human(report))
    return 1 if report.overall == "NOT READY" else 0
