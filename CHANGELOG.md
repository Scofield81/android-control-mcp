# Changelog

A projekt jelenleg `0.x.x` fejlesztési fázisban van — a valós hardveres validáció
(USB ADB, Wi-Fi ADB, mirroring, input, touchscreen, keyboard/mouse, gamepad, OTG/AOA,
broken-screen Rescue, teljesítménymérés, telepítési folyamat) lezárásáig nem lesz `1.0.0`.

Formátum: [Keep a Changelog](https://keepachangelog.com/hu/1.1.0/) alapján, lazábban.

## [Unreleased]

### Added
- Telepítési rendszer: `scripts/install_windows.ps1` (per-user, admin jog nélkül,
  dependency-detektálással), `scripts/uninstall_windows.ps1`, `.cmd` wrapper.
- `android-control-mcp doctor` (és `doctor --json`) diagnosztikai parancs.
- `android-control-mcp configure` — MCP kliens-konfigurator (VS Code / Claude Code / Generic).
- `INSTALL_WITH_AI.md`, `docs/INSTALLATION_VALIDATION.md`.
- Dokumentáció-struktúra: `docs/installation/`, `docs/usage/`, `docs/reference/`,
  `docs/development/`.
- `SECURITY.md`, `CHANGELOG.md`.
- `docs/reference/TOOLS.md` — automatikusan generált, kategorizált tool-katalógus.
- `docs/development/INTEGRATION.md` — voice/agent-integrációs útmutató.
- Read-only scrcpy mirror mód (`rescue_start_mirror(read_only=True)`), `--print-fps`
  diagnosztika.
- GitHub Issue Form sablonok, `.github/FUNDING.yml`, README támogatási szakasz (Stripe).

### Fixed
- `usb_host`/`usb_accessory` kapacitás valódi `pm list features` lekérdezésből, nem az ADB
  kapcsolat puszta létéből.
- scrcpy session startup health-check (egy gyorsan kilépő scrcpy-folyamat nem regisztrálódik
  hamisan sikeres sessionként).
- `ANDROID_CONTROL_SCRCPY_PATH` környezeti változó ténylegesen figyelembe véve (korábban a
  hibaüzenet ajánlotta, de a kód sosem olvasta ki).
- scrcpy alfolyamat stdout-ja pufferelve (korábban `DEVNULL`, a `--print-fps` kimenete
  némán elveszett volna).
- Wi-Fi vs USB ADB kapcsolat helyes megkülönböztetése a `doctor` kimenetében (mDNS-alapú
  Wi-Fi-serial korábban tévesen "USB"-ként jelent meg).

### Changed
- Támogatási összegek: 1000/2000/3000 HUF (korábbi 1000/1600/3100 HUF helyett).

## [0.1.0] — kezdeti fejlesztési állapot

- Alap MCP szerver, 71 tool: eszköz/állapot, képernyő/UI, szemantikus UI-vezérlés, input,
  alkalmazások, fájlok, rendszer-kapcsolók, workflow, rendszer, Rescue (törött kijelző).
- Két rétegű engedély-modell (SAFE/NORMAL/ADMIN mód-kapu + kockázat-alapú
  `ask_permission`).
- Shell injection védelem minden dinamikus paraméteren.
- Rescue alrendszer: kapacitás-diagnosztika, kompatibilitási adatbázis (valós OEM
  forrásokkal), hivatalos scrcpy-alfolyamat indítás (tükrözés + AOA/OTG).
