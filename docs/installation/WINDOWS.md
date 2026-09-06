# Windows telepítés

Windows a projekt **elsődleges, ténylegesen tesztelt** fejlesztési/futtatási platformja.

## A) Automatizált telepítő (ajánlott)

Nem kell tudnod, mi az ADB, a Python virtualenv vagy a PATH — a szkript ezt kezeli.

```powershell
git clone https://github.com/Scofield81/android-control-mcp.git
cd android-control-mcp
.\scripts\install_windows.ps1
```

Vagy dupla-kattintással: `scripts\install_windows.cmd`.

Egyéni telepítési mappával:

```powershell
.\scripts\install_windows.ps1 -InstallDir "D:\Programok\AndroidControlMCP"
```

**Mit csinál:**

1. Ellenőrzi, van-e már megfelelő **Python (3.10+)**, **ADB** és **scrcpy** — ha igen,
   **azt** használja, nem telepít duplikátumot.
2. Hiányzó függőségnél megkérdezi, telepítse-e hivatalos forrásból (winget:
   `Python.Python.3.12`, `Google.PlatformTools`, `Genymobile.scrcpy`) — nem tesz semmit
   megerősítés nélkül.
3. Létrehoz egy **saját, izolált** könyvtárat (alap: `%LOCALAPPDATA%\AndroidControlMCP`),
   benne saját `venv`-vel — a rendszer/globális Python-környezetet nem szennyezi.
4. Telepíti a csomagot a saját venv-be.
5. Lefuttatja a [`doctor`](../usage/GETTING_STARTED.md#doctor) diagnosztikát.

**Nem kér admin jogot** — per-user telepítés (a winget csomagok többsége is per-user
telepíthető; ha egy adott gépeden csak rendszerszintű winget-telepítés engedélyezett, a
winget saját UAC-promptja kérheti — ez a winget viselkedése, nem a szkripté).

## Eltávolítás

```powershell
.\scripts\uninstall_windows.ps1
```

Ez **csak** a saját telepítési könyvtárat törli (app/venv/config/logs) — a rendszerszinten
telepített Python/ADB/scrcpy-t **nem** érinti, mert azokat más program is használhatja.

## B) Kézi telepítés

Ha inkább magad csinálnád végig, vagy testreszabott környezetbe telepítenél: lásd
[MANUAL.md](MANUAL.md).

## C) AI-fejlesztői ügynökkel

Ha VS Code Copilot/Claude Code/más coding agent van kéznél, add át neki a repository
gyökerében lévő [`INSTALL_WITH_AI.md`](../../INSTALL_WITH_AI.md) promptját.

## Következő lépés

Telepítés után: [MCP kliens beállítása](../usage/MCP_CLIENTS.md).
