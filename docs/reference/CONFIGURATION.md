# Konfiguráció

## Konfigurációs fájl

Alap hely: `~/.config/android-control-mcp/config.json` (Windows: `%APPDATA%\android-control-mcp\config.json`),
vagy az `ANDROID_CONTROL_CONFIG` környezeti változóval felülírható. Lásd a repo gyökerében
lévő [`config.example.json`](../../config.example.json) sablont.

## Környezeti változók

A környezeti változók mindig felülírják a config fájlt.

| Változó | Cél | Alapérték |
|---|---|---|
| `ANDROID_CONTROL_MODE` | Induláskori mód (egyben felső határ is — lásd [SECURITY_MODEL.md](SECURITY_MODEL.md)): `safe` / `normal` / `admin` | `normal` |
| `ANDROID_CONTROL_AUTO_APPROVE` | `1`/`true` esetén a kockázatos műveletek elicit-visszaigazolás nélkül is lefutnak (csak zárt, megbízható környezetben ajánlott) | kikapcsolva |
| `ANDROID_CONTROL_DEFAULT_SERIAL` | Alapértelmezett eszköz-serial, ha több eszköz van csatlakoztatva és a hívó nem adja meg | — |
| `ANDROID_CONTROL_ADB_PATH` | Az `adb` bináris explicit útvonala (ha nincs a PATH-on) | `adb` |
| `ANDROID_CONTROL_SCRCPY_PATH` | A `scrcpy` bináris explicit útvonala (ha nincs a PATH-on és nem a tipikus telepítési helyeken van) | automatikus felismerés |
| `ANDROID_CONTROL_AUDIT_LOG` | Az audit-napló fájl útvonala | `~/.local/state/android-control-mcp/audit.log` |
| `ANDROID_CONTROL_CONFIG` | A config.json explicit útvonala | lásd fent |
| `ANDROID_CONTROL_TRANSPORT` | `stdio` (alap) vagy `http` | `stdio` |
| `ANDROID_CONTROL_PORT` | HTTP transzport portja (csak `127.0.0.1`-re köt) | `8000` |

## `scrcpy` felismerési sorrend

A `detect_scrcpy()` ebben a sorrendben keresi a bináris: explicit paraméter (tool-hívás) →
`ANDROID_CONTROL_SCRCPY_PATH` → PATH → tipikus telepítési helyek (Windows: `%LOCALAPPDATA%\scrcpy`,
a winget-es `Genymobile.scrcpy` telepítési helye, `%ProgramFiles%\scrcpy`; Linux/macOS:
`/usr/bin`, `/usr/local/bin`, `/opt/homebrew/bin`).

## Telepítés-specifikus állapot

Ha az [automatizált Windows telepítőt](../installation/WINDOWS.md) használtad, a saját
telepítési könyvtárad `config\install_info.json` fájlja tartalmazza a venv Python
interpreter pontos útvonalát — ezt használja a `configure` parancs az MCP kliens-config
összeállításához.
