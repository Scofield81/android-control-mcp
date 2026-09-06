"""Rendszerszintu tool-ok: naplok, ertesitesek, shell-menekulesi ut, ujrainditas,
mentes (backup), es vezetek nelkuli ADB kapcsolat kezelese."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import Context

from ..adb import resolve_serial, run_adb, run_adb_checked, run_shell
from ..audit import audit
from ..config import Mode
from ..formatting import truncate
from ..permissions import (
    RISK_REBOOT,
    RISK_REBOOT_BOOTLOADER,
    RISK_SHELL_RUN,
    RiskLevel,
    ask_permission,
    require_mode,
)
from .common import SerialArg


def register(mcp) -> None:

    @mcp.tool()
    async def logcat_tail(lines: int = 200, filter_tag: str = "", serial: SerialArg = None) -> str:
        """Az utolso N sor a rendszernaplobol (logcat) - hibakereseshez.

        filter_tag megadasaval csak az adott tag-re/prioritasra szurt sorokat kapod
        (pl. 'MyApp:V *:S' csak a sajat app verbose logjait mutatja).
        """
        real_serial = await resolve_serial(serial)
        lines = max(1, min(lines, 2000))
        tag_arg = f" {filter_tag}" if filter_tag else ""
        out = await run_shell(f"logcat -d -t {lines}{tag_arg}", serial=real_serial, timeout=20.0)
        return truncate(out)

    @mcp.tool()
    async def list_notifications(serial: SerialArg = None) -> str:
        """Az eszkozon jelenleg aktiv ertesitesek osszefoglaloja (dumpsys notification)."""
        real_serial = await resolve_serial(serial)
        out = await run_shell("dumpsys notification --noredact", serial=real_serial, timeout=15.0)

        blocks: list[str] = []
        current: list[str] = []
        for line in out.splitlines():
            if line.strip().startswith("NotificationRecord("):
                if current:
                    blocks.append("\n".join(current))
                current = [line.strip()]
            elif current and ("android.title" in line or "android.text" in line or "pkg=" in line):
                current.append("  " + line.strip())
        if current:
            blocks.append("\n".join(current))

        if not blocks:
            return "Nincs aktiv ertesites (vagy a dumpsys kimenete nem parszolhato ezen az Android verzion)."
        return truncate("\n\n".join(blocks[:30]))

    @mcp.tool()
    async def running_processes(serial: SerialArg = None) -> str:
        """Aktualisan futo folyamatok listaja az eszkozon (ps -A rovidítve)."""
        real_serial = await resolve_serial(serial)
        out = await run_shell("ps -A -o PID,PPID,RSS,NAME 2>/dev/null || ps", serial=real_serial)
        return truncate(out.strip())

    @mcp.tool()
    async def wait(seconds: float) -> str:
        """Egyszeru varakozas - kepernyoatmenetek/betoltodesek kivarasahoz.

        Ha egy konkret szoveg megjelenesere varsz, a 'wait_for_text' tool
        hatekonyabb (nem var feleslegesen tovabb, ha a szoveg mar hamarabb megjelenik).
        """
        seconds = max(0.0, min(30.0, seconds))
        await asyncio.sleep(seconds)
        return f"Vartunk {seconds} masodpercet."

    @mcp.tool()
    async def shell_run(command: str, ctx: Context, serial: SerialArg = None,
                         timeout_seconds: float = 30.0) -> str:
        """Tetszoleges shell parancs futtatasa az eszkozon ('adb shell').

        Ez a menekulesi ut olyan muveletekhez, amikre nincs kulon tool. Mindig a
        legspecifikusabb tool-t reszesitsd elonyben (pl. 'tap' a 'shell_run(\"input
        tap ...\")' helyett) - igy a naplok es a megerosites-kerdesek is
        ertelmezhetobbek maradnak. Kozepes kockazatunak szamit, megerositest ker.
        """
        require_mode(Mode.NORMAL, what="tetszoleges shell parancs")
        risk, reason = RISK_SHELL_RUN
        await ask_permission(ctx, action=f"shell parancs: {command[:200]}", details=reason,
                              risk=risk, serial=serial)
        real_serial = await resolve_serial(serial)
        out = await run_shell(command, serial=real_serial,
                               timeout=max(1.0, min(timeout_seconds, 120.0)))
        audit("shell_run", serial=real_serial, command=command)
        return truncate(out)

    @mcp.tool()
    async def reboot(ctx: Context, mode: str = "normal", serial: SerialArg = None) -> str:
        """Eszkoz ujrainditasa. mode: 'normal', 'recovery' vagy 'bootloader'.

        'bootloader'/'recovery' mod magasabb kockazatu - onnan a normal
        hasznalathoz altalaban kulon (fizikai gombos) muvelet vagy flash-eles
        szukseges, ezert erosebb megerositest ker.
        """
        require_mode(Mode.NORMAL, what="ujrainditas")
        mode = mode.lower().strip()
        if mode not in ("normal", "recovery", "bootloader"):
            return "Ervenytelen mod. Hasznalj: normal, recovery, bootloader."

        risk, reason = RISK_REBOOT_BOOTLOADER if mode != "normal" else RISK_REBOOT
        await ask_permission(ctx, action=f"Ujrainditas ({mode})", details=reason,
                              risk=risk, serial=serial)

        real_serial = await resolve_serial(serial)
        args = ["reboot"] if mode == "normal" else ["reboot", mode]
        await run_adb_checked(args, serial=real_serial, timeout=15.0)
        audit("reboot", serial=real_serial, mode=mode)
        return f"Ujrainditas elinditva ({mode})."

    @mcp.tool()
    async def backup_apps_data(local_path: str, ctx: Context, include_system: bool = False,
                                serial: SerialArg = None) -> str:
        """Teljes ADB mentes keszitese az eszkozrol egy .ab fajlba a szamitogepen.

        FONTOS: ez a standard Android `adb backup` funkciot hasznalja, ami CSAK
        olyan eszkozon mukodik, ahol az ADB hibakereses mar korabban engedelyezve
        lett (a telefon oldalan). A mentes soran a telefon kepernyojen jovahagyast
        (es esetleg jelszot) kerhet - ha a kepernyo torott, ez akadaly lehet, de
        ez az Android sajat mechanizmusa, nem ezen eszkoz korlatja.
        """
        require_mode(Mode.NORMAL, what="teljes eszkoz-mentes")
        await ask_permission(
            ctx, action=f"Teljes ADB mentes -> {local_path}",
            details="Az osszes (vagy a kivalasztott) alkalmazas adatai egy fajlba kerulnek.",
            risk=RiskLevel.LOW,
            serial=serial,
        )
        real_serial = await resolve_serial(serial)
        args = ["backup", "-f", local_path, "-apk"]
        if include_system:
            args += ["-system"]
        else:
            args += ["-noshared"]
        args += ["-all"]
        await run_adb_checked(args, serial=real_serial, timeout=600.0)
        audit("backup_apps_data", serial=real_serial, local=local_path)
        return f"Mentes elkeszult: {local_path}"

    @mcp.tool()
    async def connect_wifi(host_port: str) -> str:
        """Kapcsolodas vezetek nelkuli ADB-vel ('adb connect ip:port').

        Elotte a telefonon be kell kapcsolni a Fejlesztoi beallitasok > Vezetek
        nelkuli hibakereses funkciot, ami megadja a cimet/portot (vagy egy
        parositasi kodot ujabb Android verziokon - azt kulon kell parositani
        'adb pair'-rel, amit ez a tool jelenleg nem fed le).
        """
        result = await run_adb(["connect", host_port], timeout=15.0)
        audit("connect_wifi", target=host_port, ok=result.returncode == 0)
        return result.stdout.strip() or result.stderr.strip()

    @mcp.tool()
    async def disconnect_device(serial: SerialArg = None) -> str:
        """Vezetek nelkuli ADB kapcsolat bontasa egy eszkozzel."""
        real_serial = await resolve_serial(serial)
        result = await run_adb(["disconnect", real_serial], timeout=10.0)
        return result.stdout.strip() or f"Lecsatlakoztatva: {real_serial}"
