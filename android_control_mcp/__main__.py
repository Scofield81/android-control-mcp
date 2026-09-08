"""Belepesi pont: `python -m android_control_mcp` vagy az 'android-control-mcp' parancs."""

from __future__ import annotations

import argparse
import sys

from . import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="android-control-mcp",
        description="Android Control MCP szerver - Android eszkoz-vezerlo MCP ADB-n keresztul.",
    )
    parser.add_argument("--version", action="version", version=f"android-control-mcp {__version__}")
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="Kilistazza a regisztralt toolokat es kilep (nem indit szervert).",
    )
    parser.add_argument(
        "--devices",
        action="store_true",
        help="Kilistazza a csatlakoztatott Android eszkozoket es kilep.",
    )

    subparsers = parser.add_subparsers(dest="command")

    doctor_parser = subparsers.add_parser(
        "doctor", help="PC-oldali diagnosztika (Python/ADB/scrcpy/config/MCP-tool-ok)."
    )
    doctor_parser.add_argument("--json", action="store_true", help="Gepi olvashato JSON kimenet.")

    configure_parser = subparsers.add_parser(
        "configure", help="MCP kliens-konfigurator (VS Code / Claude Code / Generic)."
    )
    configure_parser.add_argument("--client", choices=["vscode", "claude-code", "generic", "none"])
    configure_parser.add_argument("--scope", help="pl. user/project (VS Code), local/project/user (Claude Code)")
    configure_parser.add_argument("--workspace-dir", help="Workspace/project konyvtar (alap: jelenlegi konyvtar).")

    args = parser.parse_args()

    if args.command == "doctor":
        from .doctor import main_doctor

        sys.exit(main_doctor(as_json=args.json))

    if args.command == "configure":
        from .cli_configure import main_configure

        sys.exit(main_configure(client=args.client, scope=args.scope, workspace_dir=args.workspace_dir))

    if args.devices:
        import asyncio

        from .adb import list_devices

        devices = asyncio.run(list_devices())
        if not devices:
            print("Nincs csatlakoztatott eszkoz.")
        for d in devices:
            print(f"  {d.serial}  [{d.state}]")
        sys.exit(0)

    from .server import mcp, run

    if args.list_tools:
        try:
            tools = sorted(mcp._tool_manager._tools)  # type: ignore[attr-defined]
        except AttributeError:
            tools = []
        print(f"{len(tools)} tool:")
        for name in tools:
            print(f"  - {name}")
        sys.exit(0)

    run()


if __name__ == "__main__":
    main()
