# Android Control MCP

**Magyar** | English (hamarosan)

📖 [Dokumentáció](#dokumentáció) · 🐛 [Hibajelentés](../../issues/new?template=bug_report.yml) ·
💡 [Funkciójavaslat](../../issues/new?template=feature_request.yml) ·
💬 [Discussions](../../discussions) · ☕ [Támogatás](#-támogasd-a-fejlesztést)

---

**71 tool** egy komplett **Android eszköz-vezérlő** MCP szerverben. Nem csak „futtasd ezt az
ADB parancsot” – hanem „**kezeld a telefont/tabletet**”: szemantikus UI-vezérlés
(`tap_element`, `type_into` — nincs szükség koordináta-számolásra), képernyőkép/-felvétel,
opcionális OCR-fallback, alkalmazáskezelés, fájlműveletek, rendszer-kapcsolók, naplók,
értesítések, magasabb szintű workflow-tool-ok, és egy **Rescue mód** törött kijelzőjű/nem
elérhető eszközök diagnosztikájához és adatmentéséhez — mindezt strukturált UI-hierarchiával,
hogy a modellnek ne kelljen képfelismeréssel találgatnia, hova kell koppintani. Lásd a teljes
[tool-katalógust](docs/reference/TOOLS.md).

Elsődlegesen **Windows**-on fejlesztve és valós eszközön tesztelve, de mivel tisztán a
szabványos `adb` binárisra épül, macOS-en és Linuxon is működik (⚠️ ez utóbbi kettő **még
nincs valós gépen validálva** — lásd [docs/installation/LINUX.md](docs/installation/LINUX.md)).
USB-n és vezeték nélküli (Wi-Fi) ADB-n keresztül is, tetszőleges számú csatlakoztatott
eszközzel.

---

## ⚠️ Fontos határ

Ez az eszköz **nem képes és nem is célja** képernyőzár vagy más hozzáférés-védelem
**jogosulatlan** megkerülése — sem PIN/minta próbálgatás (brute force), sem exploit, sem
titkosítás-megkerülés. A legtöbb funkció csak olyan eszközön működik, amelyen a **USB
hibakeresés** már korábban engedélyezve/jóváhagyva lett a készülék saját képernyőjén — ez az
Android beépített biztonsági mechanizmusa.

Részletek (beleértve a Rescue mód ADB-mentes AOA/OTG útját, és mikor tud/nem tud ez a
szoftver mit kezdeni egy zárolt eszközzel): [docs/reference/SECURITY_MODEL.md](docs/reference/SECURITY_MODEL.md)
és [docs/usage/RESCUE.md](docs/usage/RESCUE.md) "A kemény korlát" szakasza.

---

## Gyors telepítés

**Windows (automatizált, laikusnak is):**

```powershell
git clone https://github.com/Scofield81/android-control-mcp.git
cd android-control-mcp
.\scripts\install_windows.ps1
```

Ellenőrzi a függőségeket (Python/ADB/scrcpy — csak hiányzót telepít, hivatalos forrásból),
saját izolált könyvtárba/venv-be telepít, admin jog nélkül. Részletek:
[docs/installation/WINDOWS.md](docs/installation/WINDOWS.md).

**AI fejlesztői ügynökkel** (VS Code Copilot, Claude Code, más coding agent): add át neki az
[INSTALL_WITH_AI.md](INSTALL_WITH_AI.md) promptját.

**Kézzel / Linux / macOS:** [docs/installation/MANUAL.md](docs/installation/MANUAL.md) ·
[docs/installation/LINUX.md](docs/installation/LINUX.md) (⚠️ még nem validált).

## Gyors használat

```bash
android-control-mcp doctor          # diagnosztika: Python/ADB/scrcpy/eszközök/71 tool
android-control-mcp configure       # MCP kliens beállítása (VS Code / Claude Code / Generic)
ANDROID_CONTROL_MODE=normal android-control-mcp
```

Részletek: [docs/usage/GETTING_STARTED.md](docs/usage/GETTING_STARTED.md) ·
[docs/usage/MCP_CLIENTS.md](docs/usage/MCP_CLIENTS.md).

Néhány példa arra, mit jelent a "tool" a gyakorlatban:

> **„Nézd meg, milyen a telefon, és mennyi a szabad hely.”**
> `device_info` → `storage_usage` → `battery_status`

> **„Nyisd meg a Naptárat, hozz létre egy találkozót holnapra, majd térj vissza a főképernyőre.”**
> `launch_app("com.google.android.calendar")` → `ui_dump` → `tap`/`type_text` a mezőkön →
> mentés gombra `tap` → `press_key("home")`

> **„Mentsd le a fotóimat a gépre.”**
> `list_files("/sdcard/DCIM/Camera")` → `pull_file` minden fájlra

> **„Görgess le, amíg megtalálod az Adatvédelem menüpontot, és nyisd meg.”**
> `scroll_to("Adatvédelem")` → `tap_element(text="Adatvédelem")`

## Miért más, mint egy `adb shell` wrapper?

Szemantikus UI-vezérlés (`tap_element(text="Bejelentkezés")` — kereső+cselekvő egy hívásban)
koordináta-hurcolás helyett, `wait_for_text`/`wait_until_screen_changes` fix `sleep` helyett,
`SAFE`/`NORMAL`/`ADMIN` mód + kockázat-alapú megerősítés visszafordíthatatlan műveleteknél,
shell injection védelem minden dinamikus paraméteren. Részletek:
[docs/reference/SECURITY_MODEL.md](docs/reference/SECURITY_MODEL.md).

## Rescue mód — törött kijelzőjű/nem elérhető eszközök

Ha a telefon kijelzője törött (nem lehet feloldani), de saját eszközödről van szó és korábban
**már** engedélyezted az USB hibakeresést, vagy a telefon támogat vezetékes külső kijelzőt —
a Rescue mód segít diagnosztizálni és adatot menteni. **Ez NEM lockscreen-bypass/brute-force
eszköz.** Minden kapacitás-érték `supported`/`unsupported`/**`unknown`** — sosem találunk ki
támogatást. Részletek: [docs/usage/RESCUE.md](docs/usage/RESCUE.md),
[docs/reference/COMPATIBILITY.md](docs/reference/COMPATIBILITY.md).

## Tool-katalógus (71 tool)

| Kategória | Db |
|---|--:|
| Eszköz / állapot | 8 |
| Képernyő / „látás” | 6 |
| Szemantikus UI-vezérlés | 5 |
| Bemenet / gesztusok | 9 |
| Alkalmazások | 8 |
| Fájlok | 8 |
| Rendszer-kapcsolók | 6 |
| Workflow (összetett) | 4 |
| Rendszer | 9 |
| Rescue (törött kijelző) | 8 |

Teljes, kategorizált, mód/read-only-jelölt lista: [docs/reference/TOOLS.md](docs/reference/TOOLS.md)
(mindig aktuális parancssoros változat: `android-control-mcp --list-tools`).

## Voice/agent-integráció

Az Android Control MCP nem egyetlen kliens (pl. Claude Code) kiegészítője, hanem önálló MCP
szerver — voice assistant, saját agent, JARVIS-szerű rendszer mögé is illeszthető. Lásd
[docs/development/INTEGRATION.md](docs/development/INTEGRATION.md).

## Fejlesztés

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check .
```

**Nincs GitHub Actions CI** — a tesztelés helyben történik. Részletek:
[docs/development/DEVELOPMENT.md](docs/development/DEVELOPMENT.md).

---

## Dokumentáció

**Telepítés:** [Windows](docs/installation/WINDOWS.md) ·
[Linux](docs/installation/LINUX.md) (⚠️ nem validált) ·
[Kézi/MANUAL](docs/installation/MANUAL.md) · [AI-ügynökkel](INSTALL_WITH_AI.md) ·
[Validációs checklist](docs/INSTALLATION_VALIDATION.md)

**Használat:** [Első lépések](docs/usage/GETTING_STARTED.md) ·
[MCP kliensek](docs/usage/MCP_CLIENTS.md) · [Rescue mód](docs/usage/RESCUE.md) ·
[Tükrözés](docs/usage/MIRRORING.md) · [Gaming (roadmap)](docs/usage/GAMING.md)

**Referencia:** [Tool-katalógus](docs/reference/TOOLS.md) ·
[Konfiguráció](docs/reference/CONFIGURATION.md) ·
[Kompatibilitás](docs/reference/COMPATIBILITY.md) ·
[Biztonsági modell](docs/reference/SECURITY_MODEL.md)

**Fejlesztőknek:** [Fejlesztői útmutató](docs/development/DEVELOPMENT.md) ·
[Integráció (voice/agent)](docs/development/INTEGRATION.md) ·
[Benchmarking (roadmap)](docs/development/BENCHMARKING.md)

**Egyéb:** [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) ·
[CHANGELOG.md](CHANGELOG.md)

---

## Visszajelzés, hibajelentés, ötletek

Ha hibát találsz, nyiss egy **[hibajelentést](../../issues/new?template=bug_report.yml)**;
funkció-ötlethez egy **[funkciójavaslatot](../../issues/new?template=feature_request.yml)**;
ha egy telefonodon kipróbáltad a Rescue módot, egy
**[eszköz-kompatibilitási bejelentést](../../issues/new?template=device_compatibility.yml)**
— ez utóbbi közvetlenül segít bővíteni a kompatibilitási adatbázist (előbb ellenőrizzük,
mielőtt hivatalos bejegyzésként bekerülne).

Kérdéshez, beszélgetéshez, ötleteléshez inkább a **[Discussions](../../discussions)**
felület való, nem az Issues. Kód-hozzájárulást (pull request) egyelőre nem fogadunk — lásd
[CONTRIBUTING.md](CONTRIBUTING.md) és a [Licenc](#licenc) szakaszt.

---

## ☕ Támogasd a fejlesztést

Az Android Control MCP ingyenesen használható.
Ha hasznosnak találod a projektet és szeretnéd támogatni a további fejlesztést, ezt
teljesen önkéntesen megteheted.

A támogatás nem szükséges az ingyenes verzió használatához, és nem biztosít külön
funkciókat vagy előnyöket.

| | Összeg | |
|---|---:|---|
| ☕ Kávé | 1 000 Ft | [Támogatom →](https://donate.stripe.com/00w8wQbRu4Vzfzn3JP38400) |
| ☕☕ Fejlesztés támogatása | 2 000 Ft | [Támogatom →](https://donate.stripe.com/eVq5kEf3G3Rv9aZ2FL38403) |
| 🚀 Nagy támogatás | 3 000 Ft | [Támogatom →](https://donate.stripe.com/dRmeVe4p22Nr2MB1BH38404) |

Mindhárom a Stripe saját, biztonságos fizetési oldalára visz (bankkártya, Apple Pay, Google
Pay) — egyszeri, önkéntes tranzakció, nincs hozzá szükség Android Control MCP fiókra.

## Licenc

A forráskód nyilvánosan olvasható ezen a repón, de **nem MIT/nyílt forráskódú licenc** alatt
áll. Letölthető, telepíthető és szabadon használható, de **továbbterjesztése, kereskedelmi
forgalomba hozatala és módosított változatának közzététele a szerző előzetes, írásos engedélye
nélkül nem megengedett.** A teljes feltételek: [`LICENSE`](LICENSE).
