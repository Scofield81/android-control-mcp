"""'android-control-mcp configure' - MCP kliens-konfigurator.

Harom celkliens tamogatott:
  - VS Code: hivatalos .vscode/mcp.json (workspace) VAGY a "MCP: Open User
    Configuration" parancs (user scope - a pontos user-szintu fajlutvonal
    NINCS stabilan dokumentalva a VS Code hivatalos forrasaban, ezert azt
    SOSEM talaljuk ki/irjuk felul kozvetlenul - lasd docs/usage/MCP_CLIENTS.md).
  - Claude Code: a hivatalos 'claude mcp add' CLI, ami maga kezeli a
    project/user/local scope-okat (docs.claude.com/en/mcp).
  - Generic: csak egy publikalt, vendor-fuggetlen pelda-config, mert egy
    'generic' klienshez nincs egyseges hivatalos format.

Meglevo config fajlt SOSEM irunk felul vakon: parse -> backup -> merge ->
csak a sajat bejegyzesunket modositjuk.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SERVER_NAME = "android-control"


def _resolve_server_command() -> tuple[str, list[str]]:
    """A telepitett 'android-control-mcp' vegrehajthato megkeresese - ha nincs
    PATH-on, a jelenlegi Python interpreterrel '-m android_control_mcp'-kent
    hivjuk, ami a venv-en beluli hivasnal mindig mukodik."""
    exe = shutil.which("android-control-mcp")
    if exe:
        return exe, []
    return sys.executable, ["-m", "android_control_mcp"]


def _server_entry(env_overrides: dict | None = None) -> dict:
    command, args = _resolve_server_command()
    entry = {
        "type": "stdio",
        "command": command,
        "args": args,
        "env": {"ANDROID_CONTROL_MODE": "normal", **(env_overrides or {})},
    }
    return entry


def _backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.with_suffix(path.suffix + f".backup-{stamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [FIGYELEM] {path} nem ervenyes JSON ({exc}) - ures configkent kezelve, "
              "de a hibas fajlt NEM irjuk felul biztonsagi mentes nelkul.")
        return {}


def _find_install_dir() -> Path | None:
    """Ha ez a folyamat egy 'install_windows.ps1' altal letrehozott telepitesbol
    fut (a venv sajat Pythonjaval), megtalalja az InstallDir-t a telepitesi
    marker fajl alapjan - igy a configure el tudja tarolni a sajat
    regisztracioit, amit kesobb az uninstaller biztonsagosan fel tud ajanlani
    eltavolitasra. Fejlesztoi/rendszer-Python futtataskor (nincs marker) None-t
    ad vissza - ilyenkor egyszeruen nincs hova naplozni, ez NEM hiba."""
    try:
        exe = Path(sys.executable).resolve()
    except OSError:
        return None
    # Tipikus install-layout: <InstallDir>/venv/Scripts/python.exe (Windows).
    candidate = exe.parent.parent.parent
    marker = candidate / ".android-control-mcp-install.json"
    if marker.is_file():
        return candidate
    return None


def _log_registration(kind: str, scope: str, detail: dict) -> None:
    """A sikeres MCP-kliens-regisztraciot elmenti az install sajat, helyi
    'config/mcp_registrations.json' fajljaba (ha telepitett kornyezetbol
    fut) - ez teszi lehetove, hogy az uninstaller biztonsagosan felajanlhassa
    CSAK a sajat bejegyzes eltavolitasat, anelkul hogy barmit talalgatnia
    kellene mas MCP-szerverekrol/konfiguraciokrol."""
    install_dir = _find_install_dir()
    if install_dir is None:
        return
    reg_path = install_dir / "config" / "mcp_registrations.json"
    try:
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        data = _load_json(reg_path)
        entries = data.get("registrations", [])
        entries.append({
            "kind": kind,
            "scope": scope,
            "detail": detail,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        })
        data["registrations"] = entries
        reg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"  [FIGYELEM] A regisztracio naplozasa sikertelen ({exc}) - ez nem "
              "akadalyozza a tenyleges konfiguraciot, csak az uninstaller kesobbi "
              "automatikus ajanlasat erinti.")


def configure_vscode(scope: str, workspace_dir: Path) -> None:
    entry = _server_entry()
    if scope == "project":
        path = workspace_dir / ".vscode" / "mcp.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = _load_json(path)
        data.setdefault("servers", {})
        backup = _backup(path)
        data["servers"][SERVER_NAME] = entry
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  Irva: {path}")
        if backup:
            print(f"  Biztonsagi mentes a korabbi tartalomrol: {backup}")
        print("  Ellenorzes: nyisd meg VS Code-ban ezt a mappat, majd a Command "
              "Palette-ben futtasd: 'MCP: List Servers' - az 'android-control'-nak "
              "meg kell jelennie.")
        _log_registration("vscode", "project",
                           {"config_path": str(path), "auto_removable": True})
    elif scope == "user":
        print("  A VS Code user-szintu MCP-konfiguraciojanak PONTOS fajlutvonala nincs "
              "stabilan dokumentalva a hivatalos VS Code forrasban, ezert ezt a fajlt "
              "SZANDEKOSAN nem talaljuk ki/irjuk automatikusan.")
        print()
        print("  Kezi lepesek (hivatalos VS Code mechanizmus):")
        print("  1. Nyisd meg a Command Palette-et (Ctrl+Shift+P).")
        print("  2. Futtasd: 'MCP: Open User Configuration'.")
        print("  3. A megnyilo mcp.json 'servers' kulcsa ala illeszd be:")
        print()
        print(json.dumps({SERVER_NAME: entry}, ensure_ascii=False, indent=4))
        print()
        print("  4. Mentsd el, majd 'MCP: List Servers'-szel ellenorizd.")
        _log_registration("vscode", "user",
                           {"config_path": None, "auto_removable": False,
                            "manual_note": "MCP: Open User Configuration -> torold az 'android-control' bejegyzest"})
    else:
        raise ValueError(f"Ismeretlen scope: {scope!r}")


def configure_claude_code(scope: str) -> None:
    if scope not in ("local", "project", "user"):
        raise ValueError(f"Ismeretlen scope: {scope!r} (local/project/user)")

    command, args = _resolve_server_command()
    claude_exe = shutil.which("claude")

    cli_args = [
        "claude", "mcp", "add",
        "--scope", scope,
        "--transport", "stdio",
        "--env", "ANDROID_CONTROL_MODE=normal",
        SERVER_NAME, "--", command, *args,
    ]
    printable = " ".join(f'"{a}"' if " " in a else a for a in cli_args)

    if not claude_exe:
        print("  A 'claude' CLI nem talalhato a PATH-on. Futtasd kezzel:")
        print(f"    {printable}")
        return

    print(f"  Hivatalos Claude Code CLI hasznalata (talalva: {claude_exe}).")
    print(f"  Futtatando parancs: {printable}")
    try:
        result = subprocess.run(cli_args, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"  [HIBA] A 'claude mcp add' futtatasa sikertelen: {exc}")
        print(f"  Futtasd kezzel: {printable}")
        return

    if result.returncode == 0:
        print("  Sikeres. Ellenorzes: 'claude mcp list'")
        print(result.stdout.strip())
        _log_registration("claude-code", scope,
                           {"config_path": None, "auto_removable": False,
                            "manual_note": f"claude mcp remove {SERVER_NAME}"})
    else:
        print(f"  [HIBA] 'claude mcp add' kilepesi kod {result.returncode}:")
        print(result.stderr.strip() or result.stdout.strip())
        print(f"  Probald kezzel: {printable}")


def configure_generic(out_path: Path) -> None:
    entry = _server_entry()
    example = {
        "_megjegyzes": (
            "Ez egy VENDOR-FUGGETLEN pelda. A pontos kulcsnev/format a te MCP "
            "kliensedtol fugg (pl. 'mcpServers', 'servers', 'mcp.servers' stb.) - "
            "nezd meg a sajat klienses dokumentaciodat, es ebbol az entry-bol "
            "illeszd be a 'command'/'args'/'env' mezoket a megfelelo helyre."
        ),
        "mcpServers": {SERVER_NAME: entry},
    }
    out_path.write_text(json.dumps(example, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  Generikus pelda-config irva: {out_path}")
    print("  Illeszd be/igazitsd a sajat MCP klienses config formatumodhoz.")


def main_configure(client: str | None, scope: str | None, workspace_dir: str | None) -> int:
    workspace = Path(workspace_dir) if workspace_dir else Path.cwd()

    if not client:
        print("Melyik MCP klienshez konfiguraljunk?")
        print("  1. VS Code")
        print("  2. Claude Code")
        print("  3. Generic MCP (pelda-config fajl)")
        print("  4. Egyelore egyikhez sem")
        choice = input("Valassz (1-4): ").strip()
        client = {"1": "vscode", "2": "claude-code", "3": "generic", "4": "none"}.get(choice, "none")

    if client == "none":
        print("Nincs klens-konfiguracio kivalasztva. Kesobb: 'android-control-mcp configure --client ...'")
        return 0

    if client == "vscode":
        if not scope:
            scope = input("User-level vagy Project-level konfiguracio? (user/project): ").strip().lower() or "project"
        configure_vscode(scope, workspace)
    elif client == "claude-code":
        if not scope:
            scope = input("Scope (local/project/user) [local]: ").strip().lower() or "local"
        configure_claude_code(scope)
    elif client == "generic":
        out_path = workspace / "android-control-mcp.generic-config.example.json"
        configure_generic(out_path)
    else:
        print(f"Ismeretlen kliens: {client!r} (vscode / claude-code / generic)")
        return 1

    return 0
