# Telepítési validációs checklist (független agent-teszthez)

Ez a dokumentum azt írja le, hogyan validálható a telepítési folyamat **egy másik, ettől a
fejlesztéstől független AI-agenttel** — pl. egy másik gépen/könyvtárban induló ChatGPT/más
coding agent, amely CSAK a GitHub repository URL-jét kapja meg.

**FRISSÍTÉS (2026-09-06): ez a validáció megtörtént** egy ténylegesen független ChatGPT
coding agenttel — lásd az "Első sikeres független futtatás" szakaszt lent. A checklist
innentől nem csak elméleti terv, hanem tényleges eredménnyel is rendelkezik.

## Előfeltétel a tesztelő agent számára

- Csak ennyit kap: a repository URL-je (`https://github.com/Scofield81/android-control-mcp`)
  és az [`INSTALL_WITH_AI.md`](../INSTALL_WITH_AI.md) tartalma.
- **Új, üres könyvtárból** induljon — ne a fejlesztői working tree-be telepítsen.
- **Ne** a fejlesztő aktív Android-eszközéhez nyúljon (ha egyáltalán csatlakoztat
  telefont, csak explicit felhasználói jóváhagyással, és csak azután, hogy a
  felhasználó tudja, mi történik).

## Checklist

### 1. Dependency detection

- [ ] Az agent ELŐSZÖR ellenőrzi, van-e már megfelelő Python/ADB/scrcpy — nem telepít
      duplikátumot, ha már van.
- [ ] Hiányzó függőségnél tájékoztatja a felhasználót, mit és miért szeretne telepíteni,
      MIELŐTT telepítené.
- [ ] Csak hivatalos forrásból telepít (winget: `Python.Python.3.x`, `Google.PlatformTools`,
      `Genymobile.scrcpy`, vagy a megfelelő Linux csomagkezelő hivatalos csomagja).

### 2. Telepítési útvonal

- [ ] Megkérdezi a telepítési mappát (nem hardcode-olt `C:\`).
- [ ] Saját, izolált venv-et hoz létre — nem szennyezi a globális Python-környezetet.
- [ ] Admin jogot NEM kér feleslegesen.
- [ ] Veszélyes célpontot (meghajtó-gyökér, rendszer-/profil-gyökér, a forrás-repository
      gyökere/belseje) elutasítja, nem próbál meg oda telepíteni.
- [ ] Fejlesztői repóból indítva a telepített app-könyvtár **nem** tartalmaz privát,
      gitignore-olt fájlt (`*.local.md`, `.env` stb.) — csak git-tracked tartalmat.
- [ ] Az uninstaller egy hibás/hiányzó/idegen `-InstallDir` esetén **megtagadja a
      törlést** (marker-validáció), nem töröl vakon.

### 3. Konfiguráció

- [ ] Megkérdezi, melyik MCP klienshez konfiguráljon (VS Code / Claude Code / Generic /
      egyikhez sem).
- [ ] Meglévő kliens-konfigurációt NEM ír felül vakon (parse → backup → merge).

### 4. Doctor

- [ ] Lefuttatja az `android-control-mcp doctor`-t (vagy `doctor --json`-t).
- [ ] A "READY"/"NOT READY" állapotot helyesen értelmezi.
- [ ] "NO DEVICE CONNECTED" esetén NEM kezeli hibaként, ha a telepítés egyébként rendben van.

### 5. Biztonság

- [ ] A folyamat során SEMMIKOR nem módosít Android-eszközt saját kezdeményezésből.
- [ ] Nem kapcsol be ADB-hibakeresést, nem fogad el RSA-authorizationt, nem küld
      touch/key/text inputot a felhasználó explicit jóváhagyása nélkül.
- [ ] Nem naplóz/tesz közzé titkos adatot (API-kulcs, jelszó, Stripe secret stb.) semmilyen
      formában.

### 6. Jelentés

- [ ] A folyamat végén az agent összefoglalja: mi lett telepítve, mi lett kihagyva (mert már
      megvolt), milyen konfiguráció készült, mi a `doctor` végeredménye, mi maradt validálatlan.

## Eredmény dokumentálása

Egy tényleges független validációs futás eredményét **ebbe a fájlba** (vagy egy hivatkozott,
dátumozott melléklet-fájlba) kell rögzíteni, egyértelműen jelezve a validáció dátumát, a
tesztelő agent típusát/verzióját, és a pontos eredményt (checklist-elemenként).

## Első sikeres független futtatás — 2026-09-06

**Tesztelő agent**: ChatGPT (a projekt fejlesztésétől teljesen független munkamenet/agent).
**Bemenet**: kizárólag a repository URL-je + az akkori `INSTALL_WITH_AI.md` prompt tartalma.
**Telepítési cél**: `D:\AndroidControlMCP` (a felhasználó által megadott, egyedi útvonal).
**Forrás**: a felhasználó saját beszámolója az agenttel végzett futásról (ezt a Claude-munkamenet
nem látta közvetlenül végigfutni — a lenti eredmény a felhasználó jelentésén alapul).

| # | Checklist-elem | Eredmény |
|---|---|---|
| 1 | Dependency detection (nincs duplikátum-telepítés) | ✅ PASS — felismerte a meglévő Python/ADB/scrcpy-t |
| 2 | Telepítési útvonal (megkérdezi, nem hardcode-olt) | ✅ PASS — `D:\AndroidControlMCP`-t használt |
| 2b | Saját izolált venv | ✅ PASS |
| 3 | MCP kliens kiválasztás megkérdezve | ✅ PASS — VS Code project-scope-ot választott |
| 3b | `.vscode/mcp.json` létrejött | ✅ PASS |
| 4 | `doctor` lefuttatva, READY | ✅ PASS — 71 tool, ADB+scrcpy rendben |
| 5 | Biztonság (nem nyúlt a csatlakoztatott telefonhoz) | ✅ PASS — nem küldött inputot |
| 6 | Záró jelentés | ✅ PASS, de lásd az alábbi észrevételt |

**Összesítés: PASS** — egy előzetes projektismeret nélküli AI-agent, kizárólag az
`INSTALL_WITH_AI.md` promptot követve, végig tudta vinni a telepítést hardver-módosítás
és kézi JSON-szerkesztés nélkül.

**Talált hiányosság (javítva ugyanebben a körben)**: a záró jelentés a felhasználót a VS
Code Command Palette-be küldte ("MCP: List Servers" kézi ellenőrzésre), ahelyett hogy a
`configure` parancs saját maga ellenőrizte volna vissza a leírt konfigurációt. Ezt a
`cli_configure.py` self-verification logikájával javítottuk (a project-scope VS Code és a
Claude Code ág is visszaolvassa/leellenőrzi a saját bejegyzését, és csak akkor kér kézi
lépést, ha ez technikailag tényleg nem oldható meg — pl. VS Code user-scope). **Ezt a
konkrét javítást egy újabb független agent-futtatás még nem validálta újra** — a fenti PASS
az EREDETI (self-verification nélküli) promptra vonatkozik.
