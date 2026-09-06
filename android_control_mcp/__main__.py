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
    args = parser.parse_args()

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
        except Exception:
            tools = []
        print(f"{len(tools)} tool:")
        for name in tools:
            print(f"  - {name}")
        sys.exit(0)

    run()


if __name__ == "__main__":
    main()
