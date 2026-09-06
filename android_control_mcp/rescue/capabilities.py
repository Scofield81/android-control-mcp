"""Kepesseg-lekerdezes: mit lehet (es mit NEM lehet biztosan) tudni egy adott
Android eszkozrol a helyreallitashoz szukseges csatornak szempontjabol.

Alapelv: minden ertek 'supported' | 'unsupported' | 'unknown'. Az 'unknown'
EGYENRANGU, VALID valasz - soha nem probaljuk kitalalni, hogy egy USB-C
csatlakozos telefon tud-e DisplayPortot, vagy hogy egy adott Android verzio
alapjan mire kepes a hardver. Csak akkor mondunk 'supported'/'unsupported'-ot,
ha: (a) az ADB-n keresztul lekerdezheto tenyleg megmondja, VAGY (b) a
compat_db-ben van egyertelmu, forrasolt bejegyzes az adott modellre.

Platform-tenyek (dokumentalva, NEM ellenorizve minden egyes hivasnal - ezek a
lekerdezesek alapjat adjak):
  - USB Host API: Android 3.1 / API 12+, hardverfuggo.
  - AOAv2 HID (billentyuzet/eger/gamepad emulacio ADB nelkul): Android 4.1 /
    API 16+, tovabba hardver-/OEM accessory-mode fuggo.
  - Normal scrcpy tukrozes: Android 5 / API 21+, ADB engedelyezes/authorization
    szukseges - torott/nem lathato kijelzonel ez pontosan az a lepes, ami
    tobbnyire nem elvegezheto utolag.
  - scrcpy audio: Android 11 / API 30+.
  - scrcpy --otg (AOA vezerles): NEM igenyel ADB-t, de NINCS video/audio.
  - Vezetekes video-kimenet (DisplayPort Alt Mode HDMI/DP-re): ez NEM
    Android-verzio kerdese, hanem konkret hardver/modell kepesseg - lasd
    compat_db.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..adb import AdbError, list_devices, run_shell
from . import compat_db
from .scrcpy_binary import ScrcpyInfo, detect_scrcpy

CapabilityValue = str  # "supported" | "unsupported" | "unknown"


@dataclass
class CapabilityReport:
    adb_state: str = "unknown"           # unavailable | unauthorized | authorized
    adb_authorized: CapabilityValue = "unknown"
    manufacturer: str = ""
    model: str = ""
    android_version: str = ""
    usb_host: CapabilityValue = "unknown"
    usb_accessory: CapabilityValue = "unknown"
    aoa_hid: CapabilityValue = "unknown"
    scrcpy_available: CapabilityValue = "unknown"
    scrcpy_version: str = ""
    scrcpy_mirror_possible: CapabilityValue = "unknown"
    wired_video_output: CapabilityValue = "unknown"
    displayport_alt_mode: CapabilityValue = "unknown"
    samsung_dex_wired: CapabilityValue = "unknown"
    samsung_dex_pc: CapabilityValue = "unknown"
    uvc_capture_available: CapabilityValue = "unknown"
    compat_source: str = ""
    compat_note: str = ""
    notes: list[str] = field(default_factory=list)


async def _probe_adb_state(serial: str | None) -> tuple[str, str | None]:
    """(adb_state, resolved_serial). adb_state: 'unavailable' | 'unauthorized' | 'authorized'."""
    devices = await list_devices()
    if not devices:
        return "unavailable", None

    if serial:
        match = next((d for d in devices if d.serial == serial), None)
        if match is None:
            return "unavailable", None
        return ("authorized" if match.state == "device" else "unauthorized"), serial

    authorized = [d for d in devices if d.state == "device"]
    if authorized:
        return "authorized", authorized[0].serial
    unauthorized = [d for d in devices if d.state == "unauthorized"]
    if unauthorized:
        return "unauthorized", unauthorized[0].serial
    return "unavailable", None


async def probe_capabilities(
    serial: str | None = None,
    manufacturer_hint: str = "",
    model_hint: str = "",
    scrcpy_path: str | None = None,
) -> CapabilityReport:
    """A teljes kepesseg-jelentes osszeallitasa.

    Ha az ADB nem erheto el/nincs engedelyezve (pl. torott kijelzo, sose
    jovahagyott szamitogep), a hivo megadhatja manufacturer_hint/model_hint-et
    kezzel (pl. a telefon dobozarol/matricajarol leolvasva), hogy a compat_db
    alapjan legalabb a video-kimenet kerdeseben kapjon valaszt - az
    ADB-fuggo kepessegek ilyenkor termeszetesen 'unknown' maradnak.
    """
    report = CapabilityReport()

    adb_state, resolved_serial = await _probe_adb_state(serial)
    report.adb_state = adb_state
    report.adb_authorized = {"authorized": "supported", "unauthorized": "unsupported",
                              "unavailable": "unknown"}[adb_state]

    manufacturer, model, android_version = manufacturer_hint, model_hint, ""

    if adb_state == "authorized" and resolved_serial:
        try:
            props = await run_shell(
                "getprop ro.product.manufacturer && getprop ro.product.model "
                "&& getprop ro.build.version.release",
                serial=resolved_serial, timeout=10.0,
            )
            lines = [p.strip() for p in props.strip().splitlines()]
            if len(lines) >= 3:
                manufacturer, model, android_version = lines[0], lines[1], lines[2]
        except AdbError as exc:
            report.notes.append(f"ADB lekerdezes sikertelen: {exc}")

        # FONTOS: az, hogy az ADB mukodik, MAGABAN NEM bizonyitja a USB Host
        # tamogatast - az ADB mukodhet Wi-Fi-n (vezetek nelkuli hibakereses/
        # 'adb connect') keresztul is, ahol a telefon USB-portjanak semmi koze
        # a kapcsolathoz. A tenyleges tamogatast az Android sajat system
        # feature-listajabol kerdezzuk le ('pm list features').
        try:
            features = await run_shell("pm list features", serial=resolved_serial, timeout=10.0)
            report.usb_host = (
                "supported" if "android.hardware.usb.host" in features else "unsupported"
            )
            report.usb_accessory = (
                "supported" if "android.hardware.usb.accessory" in features else "unsupported"
            )
        except AdbError as exc:
            report.notes.append(f"'pm list features' lekerdezes sikertelen: {exc}")
    else:
        report.notes.append(
            "ADB nem elerheto/nem engedelyezett - az ADB-fuggo kepessegek (usb_accessory, "
            "scrcpy_mirror_possible) 'unknown' maradnak. Ha ismered a gyartot/modellt, add "
            "meg manufacturer_hint/model_hint-kent a video-kimenet lekerdezesehez."
        )

    report.manufacturer = manufacturer
    report.model = model
    report.android_version = android_version

    scrcpy_info: ScrcpyInfo = await detect_scrcpy(explicit_path=scrcpy_path)
    report.scrcpy_available = "supported" if scrcpy_info.available else "unsupported"
    report.scrcpy_version = scrcpy_info.version or ""
    if not scrcpy_info.available:
        report.notes.append(scrcpy_info.detail)

    if report.scrcpy_available == "supported" and report.adb_authorized == "supported":
        report.scrcpy_mirror_possible = "supported"
    elif report.scrcpy_available == "unsupported":
        report.scrcpy_mirror_possible = "unsupported"
    else:
        report.scrcpy_mirror_possible = "unknown"

    entry = compat_db.lookup(manufacturer, model) if (manufacturer or model) else None
    if entry:
        report.wired_video_output = entry.wired_video_output
        report.displayport_alt_mode = entry.displayport_alt_mode
        report.samsung_dex_wired = entry.samsung_dex_wired
        report.samsung_dex_pc = entry.samsung_dex_pc
        report.compat_source = entry.source
        report.compat_note = entry.note
        if entry.aoa_otg_note:
            report.notes.append(entry.aoa_otg_note)
    else:
        report.notes.append(
            "Nincs ismert kompatibilitasi bejegyzes ehhez a gyarto/modell parhoz "
            f"({manufacturer!r} / {model!r}) - a video-kimeneti kepessegek 'unknown'. "
            "Bovitsd a compat/devices.json-t, ha megbizhato forrasod van ra."
        )

    # AOA HID (scrcpy --otg) NEM igenyel ADB-t, de a telefonnak accessory-mode
    # (android.hardware.usb.accessory) tamogatasa kell hozza. Ha ADB-n keresztul
    # MAR bebizonyosodott, hogy ez a feature hianyzik, azt megbizhatoan
    # 'unsupported'-nak jelezhetjuk - minden mas esetben (ADB nem elerheto, vagy
    # a feature jelen van) 'unknown' marad, amig a 'rescue_start_otg' tenylegesen
    # meg nem probalja (annak sikere/hibaja adja a vegleges bizonyitekot, mert
    # a feature-flag jelenlete nem garantalja, hogy a HID-vezerles gyakorlatban
    # is mukodik az adott OEM firmware-en).
    report.aoa_hid = "unsupported" if report.usb_accessory == "unsupported" else "unknown"

    report.uvc_capture_available = "unknown"  # PC-oldali USB capture-eszkoz felismerese kulon lepes

    return report


def recommend_path(report: CapabilityReport) -> str:
    """Emberi nyelvu ajanlas a jelentes alapjan - csak azt allitja, amit a
    report tenyleg tud, semmi tobbet."""
    if report.adb_authorized == "supported":
        return (
            "Az eszkoz mar engedelyezett ADB-n - hasznald a normal Android Control MCP "
            "tool-okat (screenshot, ui_dump, tap stb.), vagy a Rescue mirror-t "
            "('rescue_start_mirror') a kepernyo tukrozesehez/vezerlesehez."
        )

    if report.wired_video_output == "supported":
        return (
            "ADB nincs engedelyezve, DE az ismert modell alapjan a telefon tamogat "
            "vezetekes kulso kijelzot (USB-C -> HDMI/DisplayPort adapter). Csatlakoztass "
            "egy ilyen adaptert kulso monitorra/TV-re, es USB egerrel/billentyuzettel "
            "(vagy 'rescue_start_otg'-vel) oldd fel a zart kepernyot - utana mar a normal "
            "ADB-alapu tool-ok is hasznalhatok lesznek."
        )

    if report.scrcpy_available == "supported":
        return (
            "ADB nincs engedelyezve, es a video-kimenet ismeretlen/nem tamogatott. Probald "
            "az AOA-alapu 'rescue_start_otg'-t: ez ADB nelkul, a sajat USB "
            "billentyuzeted/egered fizikai forgalmazasaval teszi lehetove a kepernyozar "
            "feloldasat (KEP NELKUL - vakon, a telefon sajat kijelzoje alapjan, ha az meg "
            "latszik, vagy tapintassal ismert gombelrendezes alapjan)."
        )

    return (
        "Nincs eleg informacio megbizhato ajanlashoz. Ellenorizd, hogy a scrcpy telepitve "
        "van-e ('rescue_probe' ujra scrcpy_path megadasaval), es add meg a telefon "
        "gyartojat/modelljet manufacturer_hint/model_hint parameterkent, ha ismert."
    )
