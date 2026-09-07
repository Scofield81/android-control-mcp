"""Eszkoz-informacio es allapot lekerdezo tool-ok (mind SAFE modban is futnak)."""

from __future__ import annotations

from ..adb import AdbError, list_devices, resolve_serial, run_shell
from ..config import CONFIG, Mode, level_value
from ..formatting import parse_key_value_lines
from .common import SerialArg, dumpsys


def register(mcp) -> None:

    @mcp.tool()
    async def device_list() -> str:
        """Csatlakoztatott Android eszkozok listaja (USB vagy 'adb connect' wifi).

        Mutatja minden eszkoz sorozatszamat es allapotat (device/unauthorized/offline).
        Ha tobb eszkoz van, a tobbi tool 'serial' parameterevel valaszthato ki, melyiken
        fusson a muvelet.
        """
        devices = await list_devices()
        if not devices:
            return (
                "Nincs csatlakoztatott Android eszkoz. Csatlakoztass egy telefont/tabletet "
                "USB-n (es engedelyezd az USB hibakeresest a keszuleken), vagy hasznald a "
                "'connect_wifi' toolt vezetek nelkuli ADB-hez."
            )
        lines = [f"- {d.serial}  [{d.state}]" for d in devices]
        return "\n".join(lines)

    @mcp.tool()
    async def device_info(serial: SerialArg = None) -> str:
        """Az eszkoz alap adatai: gyarto, modell, Android verzio, SDK szint, build.

        Hasznos elso lepes barmilyen automatizalas elott, illetve amikor eldontendo,
        milyen Android verziora/ROM-ra frissitheto egy regebbi keszulek.
        """
        real_serial = await resolve_serial(serial)
        props = [
            "ro.product.manufacturer", "ro.product.model", "ro.product.device",
            "ro.product.board", "ro.build.version.release", "ro.build.version.sdk",
            "ro.build.version.security_patch", "ro.build.fingerprint", "ro.build.display.id",
            "ro.build.type", "ro.boot.serialno", "persist.sys.timezone",
            "ro.product.cpu.abi", "ro.build.characteristics",
        ]
        cmd = " && ".join(f"getprop {p}" for p in props)
        out = await run_shell(cmd, serial=real_serial)
        values = out.strip().splitlines()
        data = dict(zip(props, [v.strip() for v in values]))

        screen = await run_shell("wm size && wm density", serial=real_serial)

        lines = [
            f"Gyarto/modell: {data.get('ro.product.manufacturer', '?')} {data.get('ro.product.model', '?')}",
            f"Eszkoz/board kodnev: {data.get('ro.product.device', '?')} / {data.get('ro.product.board', '?')}",
            f"Android verzio: {data.get('ro.build.version.release', '?')} "
            f"(SDK {data.get('ro.build.version.sdk', '?')})",
            f"Biztonsagi patch: {data.get('ro.build.version.security_patch', '?')}",
            f"Build tipus: {data.get('ro.build.type', '?')} | Display ID: {data.get('ro.build.display.id', '?')}",
            f"CPU ABI: {data.get('ro.product.cpu.abi', '?')}",
            f"Sorozatszam: {data.get('ro.boot.serialno', real_serial)}",
            f"Fingerprint: {data.get('ro.build.fingerprint', '?')}",
            f"Kepernyo: {screen.strip()}",
        ]
        return "\n".join(lines)

    @mcp.tool()
    async def battery_status(serial: SerialArg = None) -> str:
        """Akkumulator toltottsege, allapota (tolt/lemerul), homerseklete."""
        real_serial = await resolve_serial(serial)
        out = await dumpsys("battery", serial=real_serial)
        data = parse_key_value_lines(out)
        level = data.get("level", "?")
        scale = data.get("scale", "100")
        temp = data.get("temperature")
        temp_c = f"{int(temp) / 10:.1f} °C" if temp and temp.lstrip('-').isdigit() else "?"
        status_map = {"1": "ismeretlen", "2": "tolt", "3": "kisul", "4": "nem tolt", "5": "teli"}
        status = status_map.get(data.get("status", ""), data.get("status", "?"))
        plugged_map = {"0": "nincs csatlakoztatva", "1": "AC toltő", "2": "USB", "4": "vezetek nelkuli"}
        plugged = plugged_map.get(data.get("plugged", "0"), "?")

        return (
            f"Toltottseg: {level}/{scale} ({int(int(level) / int(scale) * 100) if level.isdigit() and scale.isdigit() else '?'}%)\n"
            f"Allapot: {status}\n"
            f"Aramforras: {plugged}\n"
            f"Homerseklet: {temp_c}\n"
            f"Egeszseg: {data.get('health', '?')}"
        )

    @mcp.tool()
    async def storage_usage(serial: SerialArg = None) -> str:
        """Belso tarhely-hasznalat (df /data, /sdcard)."""
        real_serial = await resolve_serial(serial)
        out = await run_shell("df -h /data /sdcard 2>/dev/null || df /data /sdcard", serial=real_serial)
        return out.strip()

    @mcp.tool()
    async def screen_state(serial: SerialArg = None) -> str:
        """A kepernyo aktualis allapota: be/kikapcsolva, es hogy zarolva van-e.

        Informativ lekerdezes - NEM alkalmas es NEM is a celja a zarolas
        megkerulesere; csak megmutatja, mi az aktualis allapot.
        """
        real_serial = await resolve_serial(serial)
        out = await dumpsys("power", serial=real_serial, timeout=15.0)
        awake = "mWakefulness=Awake" in out
        keyguard_out = await dumpsys("window", serial=real_serial, timeout=15.0)
        locked = "mDreamingLockscreen=true" in keyguard_out or "isStatusBarKeyguard=true" in keyguard_out
        return (
            f"Kepernyo: {'BEKAPCSOLVA' if awake else 'kikapcsolva/alvo'}\n"
            f"Zarolva (becsult): {'igen' if locked else 'valoszinuleg nem'}"
        )

    @mcp.tool()
    async def network_status(serial: SerialArg = None) -> str:
        """Halozati allapot: wifi SSID (ha lekerdezheto), IP cim, mobil adat allapota."""
        real_serial = await resolve_serial(serial)
        try:
            # A "grep inet" szandekosan nem-nulla kilepesi kodot ad, ha nincs
            # talalat (pl. a wifi ki van kapcsolva, vagy meg nincs IP-je) - ez
            # NEM hiba, hanem egy teljesen normal, varhato allapot. Valos
            # eszkozon (wifi nelkul csatlakoztatva) derult ki, hogy ez
            # korabban tevesen AdbError-t dobott es az egesz tool-t elbuktatta.
            ip_out = await run_shell("ip -4 addr show wlan0 2>/dev/null | grep inet", serial=real_serial)
        except AdbError:
            ip_out = ""
        wifi_out = await dumpsys("wifi", serial=real_serial, timeout=15.0)
        data = parse_key_value_lines(wifi_out)
        return (
            f"IP cim (wlan0): {ip_out.strip() or 'nincs (wifi kikapcsolva vagy nincs adat)'}\n"
            f"Wifi allapot (dumpsys reszlet): "
            f"{data.get('Wi-Fi is', data.get('mNetworkInfo', 'lasd nyers dumpsys wifi-t'))}"
        )

    @mcp.tool()
    async def set_mode(mode: str) -> str:
        """A szerver engedely-modjanak valtasa futas kozben: 'safe', 'normal' vagy 'admin'.

        Az inditasi mod (env/config) egy FELSO HATART (max_mode) rogzit - 'set_mode'
        soha nem tud ennel magasabbra menni, akkor sem, ha kozben mar levittek a modot.
        Igy egy ADMIN inditasu szerveren SAFE -> NORMAL -> ADMIN oda-vissza szabadon
        valthato, de egy NORMAL inditasu szerver soha nem er fel ADMIN-ig set_mode-dal
        - csak az ANDROID_CONTROL_MODE=admin kornyezeti valtozoval, ujrainditva.
        """
        try:
            target = Mode(mode.lower())
        except ValueError:
            return f"Ervenytelen mod: {mode!r}. Ervenyes ertekek: safe, normal, admin."

        if level_value(target) > level_value(CONFIG.max_mode):
            return (
                f"A mod NEM valthato '{target.value.upper()}'-ra: a szerver "
                f"'{CONFIG.max_mode.value.upper()}' felso hatarral indult, ez a hatar futas "
                f"kozben nem emelheto. Inditsd ujra ANDROID_CONTROL_MODE={target.value} "
                f"kornyezeti valtozoval, ha valoban ezt szeretned."
            )
        CONFIG.mode = target
        return f"Mod valtva: {target.value.upper()} (felso hatar: {CONFIG.max_mode.value.upper()})"
