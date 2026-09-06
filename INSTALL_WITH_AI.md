# Telepítés AI fejlesztői ügynökkel

Ha AI fejlesztői ügynököt (coding agent) használsz — VS Code Copilot Agent Mode, Claude
Code, vagy bármilyen más agent —, **másold ki az alábbi promptot és add át neki**. A prompt
nem egy konkrét AI-hoz van kötve, bármelyikkel működik.

---

## A prompt

```
Az Android Control MCP egy Android eszköz-vezérlő MCP szerver, a repository:
https://github.com/Scofield81/android-control-mcp

Kérlek, telepítsd a következő lépések szerint:

1. Olvasd el a repository README.md-jét és a docs/installation/ mappa dokumentumait,
   hogy megértsd a projekt telepítési architektúráját.

2. Ellenőrizd az operációs rendszert, amin dolgozom (Windows/Linux/macOS).

3. Kérdezd meg tőlem, hova telepítsd (telepítési mappa) - ne válassz automatikusan
   rendszerszintű, hardcode-olt útvonalat (pl. ne C:\-ra).

4. Ellenőrizd, milyen függőségek vannak már telepítve a gépemen: Python (3.10+), ADB,
   scrcpy. HA egy függőség már megfelelő verzióban megvan, HASZNÁLD azt - ne telepíts
   duplikátumot.

5. Ha egy függőség hiányzik, ELŐSZÖR magyarázd el nekem röviden, mit szeretnél
   telepíteni és miért, és csak a jóváhagyásom után telepítsd. Kizárólag HIVATALOS
   forrásból telepíts (pl. Windows: winget Python.Python.3.x / Google.PlatformTools /
   Genymobile.scrcpy; Linux: a disztribúció hivatalos csomagkezelője; soha ne random
   mirror/harmadik féltől származó letöltési oldalt).

6. Telepítsd az Android Control MCP-t saját, izolált Python virtuális környezetbe (ne a
   globális Python-csomagjaim közé).

7. Kérdezd meg, melyik MCP klienshez szeretném konfigurálni:
   - VS Code
   - Claude Code
   - Generic (saját/más MCP kliens)
   - Egyelőre egyikhez sem

8. Konfiguráld BIZTONSÁGOSAN - ha már van meglévő MCP-kliens konfigurációm, NE írd felül
   vakon: olvasd be, készíts biztonsági mentést, és csak az Android Control MCP saját
   bejegyzését add hozzá/frissítsd.

9. Futtasd le a beépített diagnosztikai ellenőrzést (`android-control-mcp doctor`), és
   mutasd meg az eredményét.

10. A `configure` parancs a project-scope VS Code konfigurációt és a Claude Code
    regisztrációt SAJÁT MAGA visszaellenőrzi (visszaolvassa a fájlt / lefuttatja a
    `claude mcp list`-et), és ezt a kimenetében jelzi ("Onellenorzes: OK" vagy
    "MCP konfiguracio: KESZ es ONELLENORIZVE"). NE küldj engem külön manuális
    ellenőrzésre (pl. "nyisd meg a Command Palette-et és nézd meg"), ha a `configure`
    már jelezte, hogy az önellenőrzés sikeres volt - csak akkor kérj tőlem manuális
    lépést, ha a `configure` kimenete kifejezetten ezt írja (ez jelenleg csak a VS Code
    "user-scope" esetén fordul elő, mert annak a fájlját nem lehet biztonságosan
    megcímezni).

11. FONTOS BIZTONSÁGI SZABÁLY: a telepítés/konfigurálás során SOHA ne módosíts semmilyen
    Android-eszközt az explicit engedélyem nélkül - ne kapcsolj be ADB-hibakeresést, ne
    fogadj el semmilyen jóváhagyó párbeszédablakot a telefonon, ne küldj touch/gombnyomás/
    szövegbeviteli parancsot egy csatlakoztatott telefonnak. Ha a telepítés végén tesztelni
    szeretnéd egy valós eszközön, ELŐSZÖR kérdezz rá, és csak explicit "igen" válasz után
    csinálj bármit a telefonnal.

12. A végén adj egy TÖMÖR, KÉSZ állapotú összegzést checklist-formában (Telepítés /
    Függőségek / MCP konfiguráció / Doctor / MCP server / tool-szám), és csak azokat a
    pontokat jelöld nyitottnak/kézi teendőnek, amik ténylegesen azok - ne fogalmazz meg
    olyan utasítást felém, amit te magad (a `doctor`/`configure` kimenete alapján) már
    igazoltál.
```

---

## Miért van ez a dokumentum?

Az Android Control MCP telepítése több lépésből áll (Python-környezet, ADB, opcionálisan
scrcpy, MCP-kliens konfiguráció). A fenti prompt egy AI-ügynöknek megadja a pontos
sorrendet és a biztonsági korlátokat, hogy laikus felhasználóként se kelljen tudnod, mi az
ADB vagy a Python virtualenv — az ügynök végigvezet rajta.

## Kapcsolódó dokumentáció

- [docs/installation/WINDOWS.md](docs/installation/WINDOWS.md) — a részletes, humán-olvasásra
  szánt Windows telepítési útmutató (ugyanaz a folyamat, amit a fenti prompt is követ).
- [docs/installation/LINUX.md](docs/installation/LINUX.md) — Linux útmutató (⚠️ jelenleg NOT
  YET VALIDATED ON REAL LINUX INSTALLATION).
- [docs/INSTALLATION_VALIDATION.md](docs/INSTALLATION_VALIDATION.md) — checklist egy
  független AI-agenttel végzett telepítési teszthez.
