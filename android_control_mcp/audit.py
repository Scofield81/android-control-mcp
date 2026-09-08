"""Konnyusulyu, forgo helyi audit naplo.

Minden eszkozt erinto muveletrol egy JSON-sort ir a naplofajlba (es stderr-re
is, hogy MCP kliens oldalon is lathato legyen). Nem allit meg semmit, ha a
naplozas meghiusul - a naplozasi hiba soha nem torheti a tenyleges muveletet.
"""

from __future__ import annotations

import json
import sys
import time
from contextlib import suppress
from pathlib import Path

from .config import CONFIG

_MAX_BYTES = 2 * 1024 * 1024
_MAX_FILES = 5


def _rotate_if_needed(path: Path) -> None:
    with suppress(OSError):
        if not path.exists() or path.stat().st_size < _MAX_BYTES:
            return
        for i in range(_MAX_FILES - 1, 0, -1):
            src = path.with_suffix(f"{path.suffix}.{i}")
            dst = path.with_suffix(f"{path.suffix}.{i + 1}")
            if src.exists():
                src.replace(dst)
        path.replace(path.with_suffix(f"{path.suffix}.1"))


def audit(event: str, **fields: object) -> None:
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "event": event, **fields}
    line = json.dumps(record, ensure_ascii=False)

    with suppress(OSError):
        print(f"[audit] {line}", file=sys.stderr, flush=True)

    with suppress(OSError):
        path = CONFIG.audit_log
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        _rotate_if_needed(path)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
