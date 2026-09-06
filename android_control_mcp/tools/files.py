"""Fajlmuveletek az eszkozon: listazas, olvasas, fel-/letoltes, torles.

Minden itt szereplo utvonal `sh_quote()`-tal van idezve, mielott egy `adb
shell` parancssorba interpolalodik - igy egy '/sdcard; rm -rf /' tipusu
utvonal csak egy (nem letezo) fajlnevkent probalkozik, nem tovabbi
parancskent hajtodik vegre.
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import Context

from ..adb import resolve_serial, run_adb_checked, run_shell
from ..audit import audit
from ..config import Mode
from ..formatting import truncate
from ..permissions import RISK_DELETE_PATH, ask_permission, require_mode
from .common import SerialArg, sh_quote


def register(mcp) -> None:

    @mcp.tool()
    async def list_files(remote_path: str = "/sdcard", serial: SerialArg = None) -> str:
        """Fajlok/konyvtarak listazasa az eszkozon egy adott utvonalon."""
        real_serial = await resolve_serial(serial)
        out = await run_shell(f"ls -la {sh_quote(remote_path)}", serial=real_serial)
        return truncate(out.strip()) or "(ures konyvtar)"

    @mcp.tool()
    async def read_file(remote_path: str, max_bytes: int = 100_000, serial: SerialArg = None) -> str:
        """Szoveges fajl tartalmanak kiolvasasa az eszkozrol (log, config, stb.).

        Csak sima szoveges fajlokhoz hasznald - binaris fajlhoz a 'pull_file'-t.
        """
        real_serial = await resolve_serial(serial)
        max_bytes = max(1, min(max_bytes, 500_000))
        out = await run_shell(f"head -c {int(max_bytes)} {sh_quote(remote_path)}", serial=real_serial)
        return truncate(out)

    @mcp.tool()
    async def file_info(remote_path: str, serial: SerialArg = None) -> str:
        """Egy fajl/konyvtar metaadatai: meret, jogosultsag, modositas ideje."""
        real_serial = await resolve_serial(serial)
        quoted = sh_quote(remote_path)
        out = await run_shell(f"stat {quoted} 2>&1 || ls -la {quoted}", serial=real_serial)
        return out.strip()

    @mcp.tool()
    async def pull_file(remote_path: str, local_path: str, serial: SerialArg = None) -> str:
        """Fajl letoltese az eszkozrol a szamitogepre (`adb pull`).

        Igy lehet pl. fenykepeket, WhatsApp mediat vagy naplofajlokat menteni
        egy torott kijelzoju, de mar korabban engedelyezett (parositott) eszkozrol.
        A biztonsagos utvonal-kezeles kulon fontos, mert 'adb pull' argumentumkent
        (nem shell-stringkent) kapja meg - itt nincs is shell-injekcios felszin,
        csak a helyi celmappa letezeset ellenorizzuk.
        """
        require_mode(Mode.NORMAL, what="fajl letoltese")
        real_serial = await resolve_serial(serial)
        os.makedirs(os.path.dirname(os.path.abspath(local_path)) or ".", exist_ok=True)
        out = await run_adb_checked(["pull", remote_path, local_path], serial=real_serial, timeout=300.0)
        audit("pull_file", serial=real_serial, remote=remote_path, local=local_path)
        size = os.path.getsize(local_path) if os.path.isfile(local_path) else 0
        return f"Letoltve: {remote_path} -> {local_path} ({size} bajt)\n{out.strip()}"

    @mcp.tool()
    async def push_file(local_path: str, remote_path: str, serial: SerialArg = None) -> str:
        """Fajl feltoltese a szamitogeprol az eszkozre (`adb push`)."""
        require_mode(Mode.NORMAL, what="fajl feltoltese")
        if not os.path.isfile(local_path):
            return f"A helyi fajl nem talalhato: {local_path}"
        real_serial = await resolve_serial(serial)
        out = await run_adb_checked(["push", local_path, remote_path], serial=real_serial, timeout=300.0)
        audit("push_file", serial=real_serial, local=local_path, remote=remote_path)
        return out.strip()

    @mcp.tool()
    async def make_dir(remote_path: str, serial: SerialArg = None) -> str:
        """Uj konyvtar letrehozasa az eszkozon."""
        require_mode(Mode.NORMAL, what="konyvtar letrehozasa")
        real_serial = await resolve_serial(serial)
        await run_shell(f"mkdir -p {sh_quote(remote_path)}", serial=real_serial)
        return f"Letrehozva: {remote_path}"

    @mcp.tool()
    async def move_path(source: str, destination: str, serial: SerialArg = None) -> str:
        """Fajl/konyvtar athelyezese vagy atnevezese az eszkozon (helyben, nem a gepre)."""
        require_mode(Mode.NORMAL, what="fajl athelyezese")
        real_serial = await resolve_serial(serial)
        out = await run_shell(f"mv {sh_quote(source)} {sh_quote(destination)}", serial=real_serial)
        return out.strip() or f"Athelyezve: {source} -> {destination}"

    @mcp.tool()
    async def delete_path(remote_path: str, ctx: Context, serial: SerialArg = None) -> str:
        """Fajl vagy konyvtar torlese az eszkozon. Megerositest ker (nem visszavonhato)."""
        require_mode(Mode.NORMAL, what="fajl/konyvtar torlese")
        risk, reason = RISK_DELETE_PATH
        await ask_permission(ctx, action=f"Torles: {remote_path}", details=reason,
                              risk=risk, serial=serial)
        real_serial = await resolve_serial(serial)
        await run_shell(f"rm -rf {sh_quote(remote_path)}", serial=real_serial)
        audit("delete_path", serial=real_serial, path=remote_path)
        return f"Torolve: {remote_path}"
