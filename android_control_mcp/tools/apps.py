"""Alkalmazas-kezeles: listazas, inditas, leallitas, telepites/eltavolitas.

Minden csomagnev `validate_package_name()`-en megy at, mielott shell-stringbe
kerulne - ez nem csak idezi, hanem eleve VISSZAUTASITJA az ervenytelen formatumu
bemenetet, mielott a parancs osszeall.
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import Context

from ..adb import resolve_serial, run_adb_checked, run_shell
from ..audit import audit
from ..config import Mode
from ..permissions import (
    RISK_APP_CLEAR_DATA,
    RISK_APP_UNINSTALL,
    RISK_INSTALL_UNKNOWN_APK,
    ask_permission,
    require_mode,
)
from .common import SerialArg, sh_quote, validate_package_name


def register(mcp) -> None:

    @mcp.tool()
    async def list_apps(serial: SerialArg = None, only_third_party: bool = True) -> str:
        """Telepitett alkalmazasok csomagneveinek listaja.

        only_third_party=True (alap) eseten csak a felhasznalo altal telepitett
        (nem rendszer-) alkalmazasokat mutatja - igy nem 300+ soros rendszerlista
        jon vissza egy egyszeru kerdesre.
        """
        real_serial = await resolve_serial(serial)
        flag = "-3" if only_third_party else ""
        out = await run_shell(f"pm list packages {flag}".strip(), serial=real_serial)
        packages = sorted(
            line.split(":", 1)[1].strip() for line in out.splitlines() if line.startswith("package:")
        )
        if not packages:
            return "Nincs talalat."
        return "\n".join(packages)

    @mcp.tool()
    async def app_info(package: str, serial: SerialArg = None) -> str:
        """Egy alkalmazas reszletei: verzio, telepites datuma, engedelyek osszefoglaloja."""
        package = validate_package_name(package)
        real_serial = await resolve_serial(serial)
        out = await run_shell(f"dumpsys package {sh_quote(package)}", serial=real_serial, timeout=15.0)
        if "Unable to find package" in out or not out.strip():
            return f"Nem talalhato ilyen csomag: {package}"

        def _grab(pattern: str) -> str:
            for line in out.splitlines():
                if pattern in line:
                    return line.strip()
            return "?"

        return (
            f"Csomag: {package}\n"
            f"{_grab('versionName=')}\n"
            f"{_grab('versionCode=')}\n"
            f"{_grab('firstInstallTime=')}\n"
            f"{_grab('lastUpdateTime=')}\n"
            f"{_grab('targetSdk=')}"
        )

    @mcp.tool()
    async def launch_app(package: str, activity: str = "", serial: SerialArg = None) -> str:
        """Alkalmazas inditasa csomagnev alapjan (pl. 'com.android.settings').

        Ha az 'activity'-t nem adod meg, a rendszer alapertelmezett (launcher)
        aktivitasat inditja a 'monkey' eszkozzel - ez a legmegbizhatobb modja
        annak, hogy egy tetszoleges alkalmazast egyetlen csomagnevvel elinditsunk.
        """
        require_mode(Mode.NORMAL, what="alkalmazas inditasa")
        package = validate_package_name(package)
        real_serial = await resolve_serial(serial)
        if activity:
            target = activity if "/" in activity else f"{package}/{activity}"
            out = await run_shell(f"am start -n {sh_quote(target)}", serial=real_serial)
        else:
            out = await run_shell(
                f"monkey -p {sh_quote(package)} -c android.intent.category.LAUNCHER 1",
                serial=real_serial,
            )
        audit("launch_app", serial=real_serial, package=package, activity=activity)
        if "Error" in out or "No activities found" in out:
            return f"Hiba az inditasnal:\n{out.strip()}"
        return f"Elinditva: {package}"

    @mcp.tool()
    async def open_url(url: str, serial: SerialArg = None) -> str:
        """URL megnyitasa az alapertelmezett alkalmazasban (bongeszo, terkep, YouTube, stb.
        - az Android eldonti az intent alapjan, melyik app kezelje)."""
        require_mode(Mode.NORMAL, what="URL megnyitasa")
        real_serial = await resolve_serial(serial)
        out = await run_shell(f"am start -a android.intent.action.VIEW -d {sh_quote(url)}",
                               serial=real_serial)
        audit("open_url", serial=real_serial, url=url)
        if "Error" in out:
            return f"Hiba az URL megnyitasakor:\n{out.strip()}"
        return f"Megnyitva: {url}"

    @mcp.tool()
    async def stop_app(package: str, serial: SerialArg = None) -> str:
        """Alkalmazas eroszakos leallitasa ('force-stop') - mint a Beallitasokban."""
        require_mode(Mode.NORMAL, what="alkalmazas leallitasa")
        package = validate_package_name(package)
        real_serial = await resolve_serial(serial)
        await run_shell(f"am force-stop {sh_quote(package)}", serial=real_serial)
        audit("stop_app", serial=real_serial, package=package)
        return f"Leallitva: {package}"

    @mcp.tool()
    async def install_apk(local_path: str, ctx: Context, serial: SerialArg = None,
                           reinstall: bool = False) -> str:
        """APK telepitese a szamitogeprol az eszkozre (`adb install`).

        A local_path a GEPEDEN levo APK fajl elerhetosege (nem az eszkozon).
        Csak megbizhato forrasbol szarmazo APK-t telepits - ismeretlen forrasu
        fajl telepitesehez a szerver megerositest ker. ADMIN modot igenyel.
        """
        require_mode(Mode.ADMIN, what="APK telepitese")
        if not os.path.isfile(local_path):
            return f"A fajl nem talalhato: {local_path}"

        risk, reason = RISK_INSTALL_UNKNOWN_APK
        await ask_permission(
            ctx, action=f"APK telepitese: {os.path.basename(local_path)}",
            details=reason, risk=risk, serial=serial,
        )

        real_serial = await resolve_serial(serial)
        args = ["install"]
        if reinstall:
            args.append("-r")
        args.append(local_path)
        out = await run_adb_checked(args, serial=real_serial, timeout=120.0)
        audit("install_apk", serial=real_serial, path=local_path, result=out.strip())
        return out.strip()

    @mcp.tool()
    async def uninstall_app(package: str, ctx: Context, serial: SerialArg = None) -> str:
        """Alkalmazas eltavolitasa a csomagneve alapjan. ADMIN modot igenyel, megerositest ker."""
        require_mode(Mode.ADMIN, what="alkalmazas eltavolitasa")
        package = validate_package_name(package)
        risk, reason = RISK_APP_UNINSTALL
        await ask_permission(
            ctx, action=f"Alkalmazas eltavolitasa: {package}", details=reason,
            risk=risk, serial=serial,
        )
        real_serial = await resolve_serial(serial)
        out = await run_adb_checked(["uninstall", package], serial=real_serial, timeout=60.0)
        audit("uninstall_app", serial=real_serial, package=package, result=out.strip())
        return out.strip()

    @mcp.tool()
    async def clear_app_data(package: str, ctx: Context, serial: SerialArg = None) -> str:
        """Egy alkalmazas osszes helyi adatanak torlese (mint 'Adatok torlese' a Beallitasokban).

        Ez visszaallitja az alkalmazast telepites utani, "uj" allapotba - a
        bejelentkezesek, mentesek, gyorsitotar mind elveszik. ADMIN modot
        igenyel, megerositest ker.
        """
        require_mode(Mode.ADMIN, what="alkalmazas adatainak torlese")
        package = validate_package_name(package)
        risk, reason = RISK_APP_CLEAR_DATA
        await ask_permission(
            ctx, action=f"Alkalmazas adatainak torlese: {package}", details=reason,
            risk=risk, serial=serial,
        )
        real_serial = await resolve_serial(serial)
        out = await run_shell(f"pm clear {sh_quote(package)}", serial=real_serial)
        audit("clear_app_data", serial=real_serial, package=package, result=out.strip())
        return out.strip()
