# Rescue mód — törött kijelzőjű/nem elérhető eszközök

## A cél

Saját (vagy jogszerűen kezelt) Android eszköz kijelzőjének megtekintése/vezérlése és
adatmentés, amikor a fizikai kijelző nem használható (törött, nem érzékel érintést, vagy
egyáltalán nem világít).

## Amit ez a modul **NEM** csinál

- **Nem old fel képernyőzárat/jelszót jogosulatlanul.** Nincs PIN-próbálgatás, mintarajzoló
  brute force, exploit, vagy titkosítás-megkerülés.
- Ha a tulajdonos megadja a **saját** PIN-jét/mintáját, azt normál bemenetként kezelheted (te
  gépeled be — a program semmit nem próbál kitalálni helyetted).

## A három külön probléma

1. **Látni** a kijelzőt (video)
2. **Irányítani** a telefont (input)
3. **Lementeni** az adatokat (fájlok)

Nem mindig ugyanaz a csatorna kell mindháromhoz — ezért a `rescue_probe` tool külön-külön
deríti fel, mi elérhető.

## A kemény korlát (őszintén)

Van egy helyzet, amit **szoftverrel nem lehet általánosan megoldani**: ha az ADB soha nem
lett engedélyezve **ÉS** nincs használható kijelző **ÉS** a telefon nem támogat külső
videokimenetet **ÉS** le van zárva. Android 10+ óta a felhasználói (Credential Encrypted)
adatokhoz a feloldási hitelesítő adat szükséges — az ADB RSA-kulcs jóváhagyása is a telefon
feloldott kijelzőjén történik (Android 4.2.2 óta). Ilyenkor **nem az eszközkészlet hiányzik,
hanem nincs olyan engedélyezett csatorna, amin a telefon kiadná a titkosított adatokat** — és
ezt a program szándékosan nem próbálja megkerülni.

## Diagnosztikai tool-ok (implementálva, tesztelve — logika szinten)

- **`rescue_probe`** — teljes diagnosztika + emberi nyelvű ajánlás egyben. Ha az ADB nem
  elérhető, megadhatod kézzel a gyártót/modellt (`manufacturer_hint`/`model_hint`), hogy a
  kompatibilitási adatbázisból legalább a video-kimenet kérdésében választ kapj.
- **`device_capabilities`** — nyers kapacitás-jelentés (`supported`/`unsupported`/`unknown`
  minden mezőhöz — lásd [COMPATIBILITY.md](../reference/COMPATIBILITY.md)).
- **`explain_capability`** — egy kapacitás-jelző emberi nyelvű magyarázata.
- **`rescue_scrcpy_status`** — megtalálható-e a hivatalos scrcpy binárisom a gépen.

## Vezérlési/tükrözési tool-ok (implementálva, **REAL DEVICE TEST REQUIRED**)

- **`rescue_start_mirror`** — teljes képernyő-tükrözés + vezérlés a hivatalos scrcpy saját
  ablakában. **ADB-t igényel, már engedélyezett eszközön.** `profile`: `quality` / `balanced`
  / `low_latency` / `gaming`.
- **`rescue_start_otg`** — `scrcpy --otg`: ADB **nélküli** billentyűzet/egér-vezérlés. A
  számítógép **saját fizikai** USB billentyűzetét/egerét továbbítja a telefonnak (AOAv2 HID).
  **FONTOS: ebben a módban nincs kép és nincs hang.** Ha a kijelző még látszik (csak az
  érintés/ujjlenyomat halott), a felhasználó a saját egerével/billentyűzetével írhatja be a
  saját PIN-jét.
- **`rescue_list_sessions`** / **`rescue_stop_session`** — futó munkamenetek kezelése.

Ezek a tool-ok a **valódi, hivatalos** `scrcpy` binárist indítják alfolyamatként — nincs
saját, újraimplementált videó/vezérlő-protokoll (lásd [MIRRORING.md](MIRRORING.md), "Miért
nem a PyPI `scrcpy-client`" szakasz).

## Ajánlott munkafolyamat

```
rescue_probe(manufacturer_hint="Samsung", model_hint="Galaxy S22")
  │
  ├─ ha ADB már engedélyezett → normál Android Control MCP tool-ok, vagy
  │                              rescue_start_mirror (kényelmes, nagy képernyős vezérlés)
  │
  ├─ ha ADB nincs, de wired_video_output=supported → csatlakoztasd USB-C→HDMI/DP
  │                              adapterrel egy külső kijelzőre, oldd fel USB
  │                              egérrel/billentyűzettel (vagy rescue_start_otg-vel),
  │                              utána ADB már engedélyezhető
  │
  └─ ha ADB nincs és video-kimenet unknown/unsupported → rescue_start_otg (vak vezérlés,
                                 ha a kijelző még látszik és csak az érintés halott)
```

## Nem implementált, tervezett utak (lásd [../development/BENCHMARKING.md](../development/BENCHMARKING.md) fázisbeosztás)

- **UVC capture** (HDMI/DP → USB capture adapter → Windows ablak): P4, nincs implementálva.
  A legtöbb laptop HDMI-portja **kimenet**, nem bemenet — egy telefon HDMI-kimenetét egy
  laptophoz csak egy külön USB capture adapterrel lehet megjeleníteni.
- **DisplayLink fallback**: P4, csak dokumentált útmutató, nincs implementálva.
- **Saját MediaProjection companion app**: opcionális, jövőbeli. Android 14+ minden új
  capture session előtt új felhasználói engedélyt kér — emiatt **nem** alkalmas
  "zero-touch"/teljesen automatikus adatmentésre olyan telefonon, amit már nem lehet
  megérinteni.

## REAL DEVICE TEST PLAN

Ezt a fejlesztési menetet **nem lehetett valódi Android eszközzel tesztelni** (nem volt
csatlakoztatott telefon). Amikor lesz:

1. `rescue_probe` — ellenőrizni, hogy a jelentés ADB-authorized és unauthorized eszközön is
   helyesen jelenik-e meg.
2. `rescue_scrcpy_status` — hivatalos scrcpy telepítés után a verzió helyesen felismerve.
3. `rescue_start_mirror` — tényleg megnyílik-e a scrcpy ablak, helyesen vezérelhető-e.
4. `rescue_start_otg` — **külön, óvatos teszt**: ellenőrizni, hogy a fizikai USB
   billentyűzet/egér tényleg csak akkor megy a telefonra, amikor az OTG-ablak fókuszban van,
   és hogy a `rescue_stop_session` tényleg visszaadja az irányítást a PC-nek.
5. `rescue_list_sessions`/`rescue_stop_session` — folyamat-életciklus (PID, leállás,
   takarítás) ellenőrzése tényleges scrcpy-folyamattal.
