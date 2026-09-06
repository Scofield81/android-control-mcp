# Telepítési validációs checklist (független agent-teszthez)

Ez a dokumentum azt írja le, hogyan validálható a telepítési folyamat **egy másik, ettől a
fejlesztéstől független AI-agenttel** — pl. egy másik gépen/könyvtárban induló ChatGPT/más
coding agent, amely CSAK a GitHub repository URL-jét kapja meg.

**FONTOS**: ez a checklist jelenleg **még nem lett végrehajtva** egy ténylegesen független
agenttel — ezt a dokumentumot a jövőbeli validációhoz készítettük elő, nem egy már
megtörtént teszt eredményeként. Ne tekintsd úgy, hogy ez a validáció megtörtént, amíg egy
tényleges futtatás eredménye nincs ide/máshova dokumentálva.

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
