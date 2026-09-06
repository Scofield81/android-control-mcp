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
2. **Ellenőrzi, hogy a megadott telepítési cél biztonságos-e**, mielőtt bármit létrehozna
   — lásd "Útvonal-védelem" lent.
3. Hiányzó függőségnél megkérdezi, telepítse-e hivatalos forrásból (winget:
   `Python.Python.3.12`, `Google.PlatformTools`, `Genymobile.scrcpy`, pontos `--exact`
   csomagazonosítóval) — nem tesz semmit megerősítés nélkül. Python telepítése után a
   friss binárist **több módon is** újra megkeresi (nem csak a PATH-ra hagyatkozva), hogy
   ugyanabban a terminál-ablakban is működjön.
4. Létrehoz egy **saját, izolált** könyvtárat (alap: `%LOCALAPPDATA%\AndroidControlMCP`),
   benne saját `venv`-vel — a rendszer/globális Python-környezetet nem szennyezi.
5. Fejlesztői repóból indítva **kizárólag a git által tracked fájlokat** másolja át — a
   privát, gitignore-olt fájlok (`*.local.md`, `.env` stb.) **sosem** kerülnek a telepített
   app-könyvtárba, még akkor sem, ha a fejlesztői working tree-ben jelen vannak.
6. Minden natív parancs (`winget`/`git`/`pip`/`venv`) tényleges kilépési kódját
   ellenőrzi — hiba esetén **azonnal leáll**, sosem jelent hamis "Telepítve" üzenetet.
7. Ír egy **telepítési marker fájlt** (lásd lent), amit az eltávolító validál.
8. Telepíti a csomagot a saját venv-be, majd lefuttatja a
   [`doctor`](../usage/GETTING_STARTED.md#doctor) diagnosztikát.

**Nem kér admin jogot** — per-user telepítés (a winget csomagok többsége is per-user
telepíthető; ha egy adott gépeden csak rendszerszintű winget-telepítés engedélyezett, a
winget saját UAC-promptja kérheti — ez a winget viselkedése, nem a szkripté).

### Útvonal-védelem

A telepítő **elutasítja** az alábbi célpontokat (canonicalizált útvonalon ellenőrizve,
akkor is, ha a mappa még nem létezik):

- meghajtó-gyökér (`C:\`, `D:\` stb.);
- a Windows-, `Program Files`-, felhasználói profil- (`%USERPROFILE%`) gyökér, illetve
  önmagában a `%LOCALAPPDATA%`;
- **a forrás-repository saját gyökere, vagy annak belseje** (pl. `<repo>\installed`) — ez
  öncélúan-másoló/rekurzív problémát okozna, mivel a telepítő a repót a célba másolja;
- olyan célpont, ami **tartalmazza** a forrás-repository gyökerét.

Interaktív módban a szkript ilyenkor újra megkérdezi a mappát; szkriptelt
(`-NonInteractive`) módban egyértelmű hibával leáll.

## Eltávolítás

```powershell
.\scripts\uninstall_windows.ps1
```

Ez **csak** a saját telepítési könyvtárat törli (app/venv/config/logs) — a rendszerszinten
telepített Python/ADB/scrcpy-t **nem** érinti, mert azokat más program is használhatja.

### Marker-védelem (REFUSE TO DELETE, ha bármi nem egyezik)

Az eltávolító **csak akkor töröl**, ha a megadott célban megtalálja és sikerül
érvényesítenie a telepítő által írt `.android-control-mcp-install.json` marker fájlt:
`product_id` pontosan `android-control-mcp`, és a benne tárolt `install_dir` egyezik a
tényleges, canonicalizált célútvonallal. Ha a marker hiányzik, sérült, vagy bármelyik mező
nem egyezik — **az eltávolító megtagadja a törlést**, akkor is, ha explicit megerősítést
adsz. Ez véd a véletlenül rossz `-InstallDir`-ral indított törlés ellen. A fenti
"Útvonal-védelem" szakasz szabályai **ettől függetlenül, elsőként** futnak le — egy
veszélyes célpontot a marker megléte sem old fel.

Ha korábban `configure`-rel VS Code project-scope-ba regisztráltad a szervert, az
eltávolító felajánlja, hogy a saját `android-control` bejegyzést is eltávolítsa onnan
(biztonsági mentéssel, csak a saját bejegyzést érintve) — más MCP-szerverekhez nem nyúl.

## B) Kézi telepítés

Ha inkább magad csinálnád végig, vagy testreszabott környezetbe telepítenél: lásd
[MANUAL.md](MANUAL.md).

## C) AI-fejlesztői ügynökkel

Ha VS Code Copilot/Claude Code/más coding agent van kéznél, add át neki a repository
gyökerében lévő [`INSTALL_WITH_AI.md`](../../INSTALL_WITH_AI.md) promptját.

## Következő lépés

Telepítés után: [MCP kliens beállítása](../usage/MCP_CLIENTS.md).
