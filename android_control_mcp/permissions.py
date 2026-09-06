"""Engedely-szintek: mod-kapu + interaktiv kockazat-megerosites.

Ugyanaz a ket-retegu modell, mint a testver-projektben (ubuntu-control-mcp):

1. MOD-KAPU (SAFE / NORMAL / ADMIN) - minden tool deklaralja a minimalis
   modot, amiben egyaltalan lefuthat.
2. KOCKAZAT-KAPU (ask_permission) - a modtol fuggetlenul interaktiv
   megerositest ker minden olyan muvelethez, ami visszafordithatatlan vagy
   adatvesztessel jarhat (gyari-adatvisszaallitas-szeru torles, alkalmazas
   eltavolitasa/adatainak torlese, ujraindtas/bootloader, ismeretlen APK
   telepitese, teljes eszkoz-mentes visszaallitasa, stb.)
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .audit import audit
from .config import CONFIG, Mode, level_value


class PermissionDenied(Exception):
    """A muvelet nem engedelyezett (mod-kapu vagy felhasznaloi elutasitas)."""


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def require_mode(needed: Mode, *, what: str) -> None:
    if level_value(CONFIG.mode) < level_value(needed):
        audit("permission", result="blocked_by_mode", needed=needed.value,
              current=CONFIG.mode.value, what=what)
        raise PermissionDenied(
            f"'{what}' legalabb '{needed.value.upper()}' modot igenyel, de a szerver "
            f"most '{CONFIG.mode.value.upper()}' modban fut. Valtsd az "
            f"ANDROID_CONTROL_MODE kornyezeti valtozot, vagy hasznald a 'set_mode' toolt."
        )


class _Approval(BaseModel):
    approve: bool = Field(description="Igaz = a muvelet vegrehajthato. Hamis = elutasitva.")
    note: str | None = Field(default=None, description="Opcionalis megjegyzes a felhasznalotol.")


async def ask_permission(ctx, *, action: str, details: str, risk: RiskLevel,
                          serial: str | None = None) -> None:
    target = f"eszkoz: {serial}" if serial else "az alapertelmezett/egyetlen csatlakoztatott eszkoz"

    if CONFIG.auto_approve:
        audit("permission", result="auto_approved", action=action, risk=risk.value, target=target)
        return

    message = (
        f"⚠️  MEGERŐSÍTÉS SZÜKSÉGES ({risk.value.upper()} kockázat)\n\n"
        f"Művelet: {action}\n"
        f"Cél: {target}\n\n"
        f"Részletek:\n{details}\n\n"
        f"Engedélyezed a végrehajtást?"
    )

    try:
        result = await ctx.elicit(message=message, schema=_Approval)
    except Exception as exc:
        audit("permission", result="no_elicit", action=action, error=str(exc))
        raise PermissionDenied(
            "A muvelet megerositest igenyel, de a jelenlegi MCP kliens nem tamogatja az "
            "interaktiv kerdest (elicitation). Hasznalj olyan klienst, ami tamogatja, vagy "
            "kapcsold be az ANDROID_CONTROL_AUTO_APPROVE=1-et megbizhato kornyezetben."
        ) from exc

    action_str = getattr(result, "action", "decline")
    data = getattr(result, "data", None)
    approved = action_str == "accept" and bool(getattr(data, "approve", False))
    note = getattr(data, "note", None) if data else None

    audit("permission", result="approved" if approved else "denied", action=action,
          risk=risk.value, target=target, note=note)

    if not approved:
        raise PermissionDenied(
            f"A felhasznalo elutasitotta a muveletet: {action}."
            + (f" Megjegyzes: {note}" if note else "")
        )


# ---- Kesz kockazat-besorolasok a leggyakoribb visszafordithatatlan muveletekhez ----

RISK_APP_UNINSTALL = (RiskLevel.MEDIUM, "az alkalmazas es (alapertelmezetten) az adatai torlodnek")
RISK_APP_CLEAR_DATA = (RiskLevel.MEDIUM, "az alkalmazas osszes helyi adata (bejelentkezes, mentesek) elveszik")
RISK_INSTALL_UNKNOWN_APK = (RiskLevel.MEDIUM, "ismeretlen forrasu APK telepitese - csak megbizhato fajlt telepits")
RISK_REBOOT = (RiskLevel.LOW, "az eszkoz ujraindul, a folyamatban levo muveletek megszakadnak")
RISK_REBOOT_BOOTLOADER = (RiskLevel.HIGH, "az eszkoz bootloader/fastboot modba lep - normal hasznalatra nem indul vissza kulon beavatkozas nelkul")
RISK_FACTORY_RESET = (RiskLevel.HIGH, "GYARI ALLAPOT VISSZAALLITASA - minden felhasznaloi adat, alkalmazas es beallitas visszavonhatatlanul torlodik")
RISK_DELETE_PATH = (RiskLevel.MEDIUM, "fajl/konyvtar torlese az eszkozon - nem visszavonhato")
RISK_SHELL_RUN = (RiskLevel.MEDIUM, "tetszoleges shell parancs futtatasa az eszkozon (adb shell)")
