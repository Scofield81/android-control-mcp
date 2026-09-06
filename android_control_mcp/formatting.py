"""Kozos formazo segedfuggvenyek a tool-valaszokhoz."""

from __future__ import annotations


def human_bytes(n: int) -> str:
    value = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} TB"


def parse_key_value_lines(text: str, sep: str = ": ") -> dict[str, str]:
    """'kulcs: ertek' soronkenti szoveget dict-te alakit (pl. dumpsys reszletek)."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if sep in line:
            k, _, v = line.partition(sep)
            out[k.strip()] = v.strip()
    return out


def truncate(text: str, max_chars: int = 20000) -> str:
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    return cut + f"\n... [levagva, {len(text) - max_chars} tovabbi karakter]"
