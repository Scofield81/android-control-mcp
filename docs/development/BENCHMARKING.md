# Benchmarking — terv (nincs implementálva, nincs mért adat)

**Ebben a fejlesztési menetben nem volt csatlakoztatott Android eszköz, ezért NINCS mért FPS/
latencia/kompatibilitási eredmény ebben a dokumentumban — és nem is állítunk ilyet.** Ez egy
dokumentált mérési terv, amit a következő, valódi eszközzel végzett munkamenetben kell
végrehajtani.

## Mit fogunk mérni (tervezett `benchmark_stream`/`benchmark_input` tool-ok, nincs implementálva)

| Mérőszám | Forrás |
|---|---|
| Transport | USB vagy Wi-Fi |
| scrcpy verzió | `rescue_scrcpy_status` |
| Android verzió, telefon modell | `device_capabilities` |
| Kódek/enkóder | scrcpy saját log/kimenet |
| Célzott vs. tényleges FPS | scrcpy saját statisztika (`--print-fps` vagy hasonló) |
| Eldobott/kihagyott képkockák | scrcpy log |
| Bitrate | a beállított profil vs. tényleges |
| Indítási idő | mérve a folyamat indításától az első kép megjelenéséig |
| Host CPU/RAM | Windows Task Manager / `psutil`, ha bekötjük |
| Input-küldési latencia | ahol mérhető (pl. `adb shell input tap` végrehajtási ideje) |

## Amit **NEM** fogunk állítani

**A telefon fizikai kijelzője és a PC kijelzője közötti "glass-to-glass" késleltetés csak
külső referenciával (pl. nagy sebességű kamera, ami egyszerre látja mindkét kijelzőt)
mérhető megbízhatóan.** Szoftveres mérés (pl. időbélyeg a küldött parancsban és a scrcpy
naplójában) ezt **nem** helyettesíti — ez csak a küldési/feldolgozási időt méri, nem a
tényleges vizuális megjelenést. Ezt a dokumentumot soha nem fogjuk "glass-to-glass
latency"-ként hivatkozott, de valójában nem úgy mért számmal feltölteni.

## Manuális mérési eljárás (dokumentált terv, végrehajtandó valódi eszközzel)

1. Csatlakoztasd a telefont USB-n, futtasd `rescue_start_mirror(profile="low_latency")`-t.
2. Indíts egy stopperórát/nagy sebességű kamerát, ami egyszerre látja a telefon kijelzőjét
   ÉS a PC monitorát.
3. Érints meg egy jól látható, változó elemet a telefon kijelzőjén (pl. egy gomb, ami
   színt vált érintésre) a PC-ről küldött `tap`-pel.
4. Számold ki a kockák különbségéből (kamera FPS ismeretében) a tényleges glass-to-glass
   késleltetést.
5. Ismételd meg USB és Wi-Fi (TCP-IP ADB) módban is, ugyanazzal az eljárással, hogy
   összehasonlítható legyen.
6. Exportáld az eredményeket CSV/JSON-ba összehasonlításhoz (tervezett formátum, nincs
   implementálva).

## Fázisbeosztás (ismétlés a fő projekt sorrendjéből)

- **P0** (kész): GitHub Actions eltávolítva, hivatalos scrcpy discovery.
- **P1** (kész, logika szinten tesztelve, hardveren nem): capability manager, `rescue_probe`,
  mirror/OTG session-indítás.
- **P2** (nincs implementálva): Windows Viewer architektúra, touch/mouse/keyboard/gamepad
  koordináta-mapper.
- **P3** (nincs implementálva): gaming/keymap motor, streaming-profil finomhangolás valós
  méréssel, `benchmark_stream`/`benchmark_input` tool-ok tényleges implementációja.
- **P4** (nincs implementálva): UVC/natív-videó Rescue viewer, DisplayLink dokumentált
  fallback, bővebb gyártói adatbázis.
