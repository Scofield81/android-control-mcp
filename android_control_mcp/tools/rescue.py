"""Rescue mod tool-ok: diagnosztika + AOA/OTG-vezerles + scrcpy-tukrozes
inditasa torott kijelzoju/nem lathato/nem elerheto ADB-jű eszkozokhoz.

Cel: SAJAT vagy jogszeruen kezelt eszkoz kepernyojenek megtekintese/
vezerlese es adatmentese, amikor a fizikai kijelzo nem hasznalhato. NEM cel
es NEM tamogatott: kepernyozar/jelszo megkerulese, PIN-probalgatas, brute
force, exploit. Ha a felhasznalo megadja a SAJAT PIN-jet/mintajat, az egy
rendes bemeneti muvelet - de ezt a tool-keszlet nem probalja kitalalni vagy
automatizalni probalgatas formajaban.
"""

from __future__ import annotations

from ..config import Mode
from ..permissions import require_mode
from ..rescue import capabilities as rescue_capabilities
from ..rescue import session as rescue_session
from ..rescue.scrcpy_binary import detect_scrcpy

_CAPABILITY_EXPLANATIONS = {
    "adb_authorized": (
        "Az ADB (Android Debug Bridge) mar engedelyezve/jovahagyva van-e ehhez a "
        "szamitogephez. Ez a legtobb funkcio elofeltetele, es ALTALABAN a telefon "
        "kepernyojen egy 'USB hibakereses engedelyezese?' parbeszedet kell "
        "'Engedelyezem'-mel jovahagyni - ha ez sosem tortent meg es a kijelzo torott, "
        "ez a lepes nem potolhato szoftveresen."
    ),
    "usb_host": (
        "A telefon USB Host kepesseggel rendelkezik-e (Android 3.1+/API 12+, "
        "hardverfuggo) - ez az alapja annak, hogy a telefon mas USB-eszkozoket "
        "(pl. billentyuzetet) tudjon fogadni."
    ),
    "aoa_hid": (
        "AOAv2 (Android Open Accessory) HID mod - ezzel a szamitogep billentyuzetnek/"
        "egernek 'adja ki magat' a telefon fele, ADB NELKUL. Csak akkor derul ki "
        "biztosan, ha a 'rescue_start_otg' tool tenylegesen megprobalja."
    ),
    "wired_video_output": (
        "A telefon kepes-e a sajat kepernyokepet vezetekesen (USB-C -> HDMI/DisplayPort "
        "adapteren) kulso monitorra/TV-re kuldeni. Ez NEM Android-verzio kerdese, hanem "
        "konkret hardver/modell kepesseg - lasd docs/COMPATIBILITY.md."
    ),
    "scrcpy_mirror_possible": (
        "Van-e telepitve hivatalos scrcpy A GEPEN, ES van-e mar engedelyezett ADB-"
        "kapcsolat - ha mindketto igaz, a teljes kepernyo-tukrozes/vezerles hasznalhato."
    ),
}


def register(mcp) -> None:

    @mcp.tool()
    async def device_capabilities(serial: str | None = None, manufacturer_hint: str = "",
                                   model_hint: str = "", scrcpy_path: str = "") -> str:
        """Az eszkoz/gep helyreallitasi kepessegeinek diagnosztikaja.

        Minden ertek 'supported' | 'unsupported' | 'unknown' - az 'unknown' EGYENRANGU
        valasz, sose talalunk ki tamogatast. Ha az ADB nem erheto el (pl. torott
        kijelzo, sose jovahagyott gep), add meg manufacturer_hint/model_hint-et
        kezzel (a telefon dobozarol/beallitasokbol, ha meg hozzaferheto), hogy
        legalabb a video-kimeneti kepesseget lekerdezhessuk az ismert-modell
        adatbazisbol.
        """
        report = await rescue_capabilities.probe_capabilities(
            serial=serial, manufacturer_hint=manufacturer_hint, model_hint=model_hint,
            scrcpy_path=scrcpy_path or None,
        )
        lines = [
            f"ADB allapot: {report.adb_state} (adb_authorized={report.adb_authorized})",
            f"Gyarto/modell: {report.manufacturer or '?'} / {report.model or '?'}"
            + (f" (Android {report.android_version})" if report.android_version else ""),
            f"scrcpy: {report.scrcpy_available}" + (f" ({report.scrcpy_version})" if report.scrcpy_version else ""),
            f"scrcpy_mirror_possible: {report.scrcpy_mirror_possible}",
            f"usb_host: {report.usb_host}",
            f"aoa_hid: {report.aoa_hid} (csak tenyleges probalkozassal derul ki - 'rescue_start_otg')",
            f"wired_video_output: {report.wired_video_output}",
            f"displayport_alt_mode: {report.displayport_alt_mode}",
            f"samsung_dex_wired: {report.samsung_dex_wired}",
            f"samsung_dex_pc: {report.samsung_dex_pc}",
            f"uvc_capture_available: {report.uvc_capture_available} (PC-oldali capture-eszkoz - meg nincs automatikus felismeres)",
        ]
        if report.compat_source:
            lines.append(f"Kompatibilitasi forras: {report.compat_source}")
        if report.compat_note:
            lines.append(f"Megjegyzes: {report.compat_note}")
        for note in report.notes:
            lines.append(f"[info] {note}")
        return "\n".join(lines)

    @mcp.tool()
    async def rescue_probe(serial: str | None = None, manufacturer_hint: str = "",
                            model_hint: str = "") -> str:
        """Teljes helyreallitasi diagnosztika + emberi nyelvu ajanlas egyben.

        Ugyanazt a jelentest adja, mint a 'device_capabilities', de a vegen
        egy konkret, a tenylegesen ismert adatokra epulo javaslatot is ad,
        hogy mit erdemes kovetkezo lepeskent tenni.
        """
        report = await rescue_capabilities.probe_capabilities(
            serial=serial, manufacturer_hint=manufacturer_hint, model_hint=model_hint,
        )
        recommendation = rescue_capabilities.recommend_path(report)
        return (
            f"ADB: {report.adb_state} | scrcpy: {report.scrcpy_available} | "
            f"vezetekes video: {report.wired_video_output} | "
            f"modell: {report.manufacturer or '?'} {report.model or '?'}\n\n"
            f"JAVASOLT UT:\n{recommendation}"
        )

    @mcp.tool()
    async def explain_capability(name: str) -> str:
        """Egy kepesseg-jelzo (pl. 'wired_video_output') emberi nyelvu magyarazata."""
        explanation = _CAPABILITY_EXPLANATIONS.get(name)
        if not explanation:
            known = ", ".join(sorted(_CAPABILITY_EXPLANATIONS))
            return f"Ismeretlen kepesseg-nev: {name!r}. Ismertek: {known}"
        return explanation

    @mcp.tool()
    async def rescue_start_mirror(serial: str | None = None, profile: str = "balanced") -> str:
        """Teljes kepernyo-tukrozes es -vezerles inditasa (a hivatalos scrcpy sajat
        ablakaban). ADB-t igenyel, MAR engedelyezett eszkozon.

        profile: 'quality', 'balanced', 'low_latency' vagy 'gaming'.
        """
        require_mode(Mode.NORMAL, what="scrcpy tukrozo munkamenet inditasa")
        try:
            sess = await rescue_session.start_mirror_session(serial, profile=profile)
        except Exception as exc:
            return f"Nem sikerult elinditani: {exc}"
        return f"Tukrozes elindult (PID {sess.pid}, profil={profile}). Leallitas: 'rescue_stop_session'."

    @mcp.tool()
    async def rescue_start_otg(serial_hint: str | None = None) -> str:
        """ADB nélküli, AOA-alapú billentyűzet/egér-vezérlés indítása ('scrcpy --otg').

        FONTOS KORLÁT: ebben a módban NINCS kép és NINCS hang - a scrcpy a SAJÁT
        fizikai USB billentyűzetedet/egeredet továbbítja a telefonnak. Ha a telefon
        kijelzője még látszik (csak az érintés/ujjlenyomat halott), a saját
        egereddel/billentyűzeteddel tudsz PIN-t/mintát beírni. Ez NEM automatikus
        próbálgatás - te (a tulajdonos) írod be, amit tudsz.
        """
        require_mode(Mode.NORMAL, what="AOA/OTG munkamenet inditasa")
        try:
            sess = await rescue_session.start_otg_session(serial_hint)
        except Exception as exc:
            return f"Nem sikerult elinditani: {exc}"
        return (
            f"AOA/OTG munkamenet elindult (PID {sess.pid}). NINCS kep/hang - a sajat "
            "billentyuzeted/egered mostantol a telefonnak van tovabbitva, amig ez a "
            "munkamenet fut. Leallitas: 'rescue_stop_session'."
        )

    @mcp.tool()
    async def rescue_list_sessions() -> str:
        """A jelenleg futó (vagy nemrég leállt) Rescue munkamenetek listája."""
        sessions = rescue_session.list_sessions()
        if not sessions:
            return "Nincs aktív Rescue munkamenet."
        lines = []
        for s in sessions:
            state = "fut" if s.is_running() else "leallt"
            lines.append(f"PID {s.pid} | {s.kind} | profil={s.profile} | serial={s.serial or '-'} | {state}")
        return "\n".join(lines)

    @mcp.tool()
    async def rescue_stop_session(pid: int) -> str:
        """Egy futó Rescue munkamenet (tükrözés vagy OTG) leállítása PID alapján."""
        ok = await rescue_session.stop_session(pid)
        return f"Leallitva: PID {pid}" if ok else f"Nincs ilyen munkamenet: PID {pid}"

    @mcp.tool()
    async def rescue_scrcpy_status(scrcpy_path: str = "") -> str:
        """A hivatalos scrcpy binaris allapota ezen a gepen (megtalalhato-e, verzio)."""
        info = await detect_scrcpy(explicit_path=scrcpy_path or None)
        return info.detail
