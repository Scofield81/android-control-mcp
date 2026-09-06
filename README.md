# Android Control MCP

**52 tool** egy komplett **Android eszköz-vezérlő** MCP szerverben. Nem csak „futtasd ezt az
ADB parancsot” – hanem „**kezeld a telefont/tabletet**”: UI-automatizálás (koppintás, gépelés,
gesztusok), képernyőkép/-felvétel, alkalmazáskezelés, fájlműveletek, rendszer-kapcsolók
(wifi/bluetooth/repülő üzemmód/hangerő), naplók és értesítések – mindezt strukturált
UI-hierarchiával, hogy a modellnek ne kelljen képfelismeréssel találgatnia, hova kell
koppintani.

Elsődlegesen **Windows**-on fejlesztve és tesztelve (a legtöbb felhasználó ADB-vel Windows-on
dolgozik), de mivel tisztán a szabványos `adb` binárisra épül, macOS-en és Linuxon is működik.
USB-n és vezeték nélküli (wifi) ADB-n keresztül is, tetszőleges számú csatlakoztatott
eszközzel.

---

## Fontos határ

Ez az eszköz **nem képes és nem is célja** képernyőzár vagy más hozzáférés-védelem
jogosulatlan megkerülése. Minden funkció kizárólag olyan eszközön működik, amelyen a **USB
hibakeresés** már korábban engedélyezve és jóváhagyva lett a készülék saját képernyőjén – ez
az Android beépített biztonsági mechanizmusa, amit ez a szoftver szándékosan nem próbál
megkerülni. Ha egy eszköz zárolt és sosem lett jóváhagyva, ez a szoftver sem tud vele mit
kezdeni – ahogy semmi más, ami nem exploit/feltörő eszköz.

---

## Miért más, mint egy `adb shell` wrapper?

| Sima megközelítés | Android Control MCP |
|---|---|
| Nyers `adb shell` parancsok | **52** fókuszált tool természetes munkamegosztással |
| Találgatás képernyőkép alapján | `ui_dump`: pontos koordináták, szöveg, resource-id minden elemhez |
| Vak hozzáférés | `SAFE` / `NORMAL` / `ADMIN` mód + kockázat-alapú megerősítés visszafordíthatatlan műveleteknél |
| Fix `sleep` várakozások | `wait_for_text`: csak addig vár, amíg tényleg meg nem jelenik a keresett elem |
| Csak egy eszköz | Tetszőleges számú csatlakoztatott eszköz, `serial` paraméterrel választva |
| Nincs kontextus-tudat | `foreground_app`: a modell tudja, épp melyik alkalmazás/aktivitás van elöl |

### Sebesség — őszintén

A tiszta `adb shell input`/`screencap` út tipikusan **100-300 ms**/koppintás és lassabb
képernyőkép-készítés. Létezik gyorsabb megoldás: a [scrcpy-mcp](https://github.com/JuanCF/scrcpy-mcp)
projekt scrcpy bináris vezérlő-protokollját használva **~5-10 ms**/input és **~33 ms**/képernyőkép
sebességet ér el (10-50×-ös gyorsulás sima ADB-hez képest). Ez az Android Control MCP jelenlegi
(v0.1.0) verziójában **még nincs implementálva** — a `scrcpy`-alapú gyors bemenet/screencap a
következő verzió elsődleges célja (lásd [Fejlesztés](#fejlesztés) / GitHub Issues). Jelenleg
tisztán ADB-re épülünk, ami egyszerűbb és függőségmentes, de lassabb.

---

## Engedély-modell

### 1. réteg – mód-kapu

A szerver **egy** módban fut (`ANDROID_CONTROL_MODE`, alap: `normal`).

| Mód | Mit enged |
|---|---|
| **SAFE** | csak olvasás: `device_info`, `screenshot`, `ui_dump`, `logcat_tail`, `list_apps`, fájlolvasás |
| **NORMAL** | a fentiek **+** koppintás/gépelés/gesztusok, alkalmazás indítása/leállítása, fájlműveletek, rendszer-kapcsolók (wifi/bluetooth/repülő mód/hangerő) |
| **ADMIN** | a fentiek **+** alkalmazás eltávolítása/adattörlése, APK telepítés, újraindítás, teljes mentés, tetszőleges shell parancs |

### 2. réteg – kockázat-kapu (`ask_permission`)

A módtól függetlenül interaktív megerősítést kér minden visszafordíthatatlan/adatvesztéssel
járó művelet: alkalmazás eltávolítása, alkalmazás adatainak törlése, ismeretlen APK telepítése,
fájl/könyvtár törlése, bootloader/recovery újraindítás, tetszőleges shell parancs.

Ha a kliens nem támogatja az elicitet: a művelet **elutasításra kerül**, hacsak az
`ANDROID_CONTROL_AUTO_APPROVE=1` nincs bekapcsolva (csak zárt, megbízható környezetben).

Minden művelet **auditálva** van (stderr + opcionális naplófájl).

---

## Telepítés

```bash
git clone git@github.com:Scofield81/android-control-mcp.git
cd android-control-mcp
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
```

Ellenőrzés:

```bash
android-control-mcp --list-tools
android-control-mcp --devices
```

> **Nincs SSH kulcsod a GitHub-hoz, vagy hibát kapsz?** → **[docs/INSTALL.md](docs/INSTALL.md)**
> (letöltés minden módja, ADB telepítése/hibaelhárítás).

### Előfeltétel: ADB

Az [Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools)
csomagban található `adb` binárisnak elérhetőnek kell lennie (PATH-ban, vagy add meg az
`ANDROID_CONTROL_ADB_PATH` környezeti változóval). A telefonon/tableten pedig be kell
kapcsolni: **Beállítások → A telefonról → Szoftver-információ → koppints 7×
a Buildszámra** (fejlesztői mód bekapcsolása), majd **Fejlesztői beállítások → USB
hibakeresés**.

## Futtatás

```bash
ANDROID_CONTROL_MODE=normal android-control-mcp
```

MCP kliens (stdio) konfiguráció, pl. Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "android-control": {
      "command": "/abszolut/ut/.venv/bin/android-control-mcp",
      "env": {
        "ANDROID_CONTROL_MODE": "normal",
        "ANDROID_CONTROL_AUDIT_LOG": "~/.local/state/android-control-mcp/audit.log"
      }
    }
  }
}
```

Windows alatt a `command` a venv `Scripts\android-control-mcp.exe` útvonala.

HTTP transzport: `ANDROID_CONTROL_TRANSPORT=http ANDROID_CONTROL_PORT=8001 android-control-mcp`
(a szerver `127.0.0.1`-re köt).

## Konfiguráció

Alap hely: `~/.config/android-control-mcp/config.json` (vagy `ANDROID_CONTROL_CONFIG`). Lásd
[`config.example.json`](config.example.json). A környezeti változók felülírják a fájlt:
`ANDROID_CONTROL_MODE`, `ANDROID_CONTROL_AUTO_APPROVE`, `ANDROID_CONTROL_AUDIT_LOG`,
`ANDROID_CONTROL_DEFAULT_SERIAL`, `ANDROID_CONTROL_ADB_PATH`.

---

## Tool-katalógus (összesen 52 tool)

| Kategória | Tool-ok | Db |
|---|---|--:|
| Eszköz / állapot | `device_list` · `device_info` · `battery_status` · `storage_usage` · `screen_state` · `network_status` · `foreground_app` · `set_mode` | 8 |
| Képernyő / „látás” | `screenshot` · `screen_record` · `ui_dump` · `wait_for_text` | 4 |
| Bemenet / gesztusok | `tap` · `double_tap` · `long_press` · `swipe` · `drag` · `scroll` · `type_text` · `press_key` · `paste_clipboard` | 9 |
| Alkalmazások | `list_apps` · `app_info` · `launch_app` · `open_url` · `stop_app` · `install_apk` · `uninstall_app` · `clear_app_data` | 8 |
| Fájlok | `list_files` · `read_file` · `file_info` · `pull_file` · `push_file` · `make_dir` · `move_path` · `delete_path` | 8 |
| Rendszer-kapcsolók | `wifi_toggle` · `bluetooth_toggle` · `airplane_mode_toggle` · `set_volume` · `open_notification_panel` · `screen_orientation` | 6 |
| Rendszer | `logcat_tail` · `list_notifications` · `running_processes` · `wait` · `shell_run` · `reboot` · `backup_apps_data` · `connect_wifi` · `disconnect_device` | 9 |

Teljes, mindig aktuális lista: `android-control-mcp --list-tools`

---

## Példák

> **„Nézd meg, milyen a telefon, és mennyi a szabad hely.”**
> `device_info` → `storage_usage` → `battery_status`

> **„Kapcsold be a repülő üzemmódot.”**
> `airplane_mode_toggle(true)` — nincs szükség UI-kattintásra, egy közvetlen tool eléri.

> **„Nyisd meg a Naptárat, hozz létre egy találkozót holnapra, majd térj vissza a főképernyőre.”**
> `launch_app("com.google.android.calendar")` → `ui_dump` → `tap`/`type_text` a mezőkön →
> mentés gombra `tap` → `press_key("home")` — a tipikus "nyit → elvégzi → bezár, vissza a
> főképernyőre" mintát ez a záró `press_key("home")` adja, ahogy egy ember is tenné.

> **„Írj egy üzenetet valakinek, és zárd be az alkalmazást.”**
> `launch_app` → `ui_dump` → `tap`/`type_text` → küldés `tap` → `stop_app` (vagy `press_key("home")`)

> **„Készíts képernyőképet, és mondd meg, mi van rajta.”**
> `screenshot` → (a kép visszakerül a válaszban)

> **„Mentsd le a fotóimat a gépre.”**
> `list_files("/sdcard/DCIM/Camera")` → `pull_file` minden fájlra

> **„Nézd meg, mit ír ki a logcat, amikor megnyitom az appot.”**
> `launch_app` → rövid `wait` → `logcat_tail`

---

## Fejlesztés

```bash
pip install -e ".[dev]"
python -m py_compile $(git ls-files '*.py')
ruff check .
```

---

## Visszajelzés, hibajelentés, ötletek

Ha hibát találsz, vagy javaslatod van egy új funkcióhoz/tool-hoz, nyiss egy
**[GitHub Issue-t](../../issues)** ebben a repóban. Kód-hozzájárulást (pull request) egyelőre
nem fogadunk — lásd [CONTRIBUTING.md](CONTRIBUTING.md) és a [Licenc](#licenc) szakaszt.

## Licenc

A forráskód nyilvánosan olvasható ezen a repón, de **nem MIT/nyílt forráskódú licenc** alatt
áll. Letölthető, telepíthető és szabadon használható, de **továbbterjesztése, kereskedelmi
forgalomba hozatala és módosított változatának közzététele a szerző előzetes, írásos engedélye
nélkül nem megengedett.** A teljes feltételek: [`LICENSE`](LICENSE).
