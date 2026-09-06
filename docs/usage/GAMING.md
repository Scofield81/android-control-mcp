# Gaming mód — tervezett architektúra (nincs implementálva)

**Ez a dokumentum tervezési/roadmap dokumentum, nem egy elkészült funkció leírása.** Ebben a
fejlesztési menetben nem volt sem csatlakoztatott Android eszköz, sem idő egy teljes
keymapping-motor hardveren validált implementálására — az alábbiak a P3-as fázis terve.

## Cél

`rescue_start_mirror(profile="gaming")` már ma is elindítja a scrcpy-t magas FPS-ű,
alacsony-latenciájú profillal (lásd [MIRRORING.md](MIRRORING.md)) — ez a valódi "gaming
mód" alapja, natív egér/billentyűzet-továbbítással, amit a scrcpy már ma is tud.

A tervezett bővítés egy **keymapping-réteg** lenne, ami touch-only játékokhoz billentyűzet/
gamepad-vezérlést tenne lehetővé.

## Tanulmányozandó referencia: QtScrcpy keymapping

A [barry-ran/QtScrcpy](https://github.com/barry-ran/QtScrcpy) projekt keymap-motorja adja az
architekturális mintát (**nem** másolva kódszinten, csak a koncepció):

- billentyű → egyszeri koppintás (tap)
- billentyű lenyomva tartva → touch hold
- WASD → virtuális joystick (körkörös terület, irány+intenzitás)
- egérmozgatás → touch drag ("mouse look")
- swipe, dupla koppintás, multi-tap

## Tervezett saját formátum

Normalizált (0.0–1.0) koordináták, NEM fix pixelek — hogy a profil különböző felbontású
kijelzőkön/orientációkban is érvényes maradjon. Mezők:

```json
{
  "orientation": "landscape",
  "bindings": [
    {"key": "space", "action": "tap", "x": 0.5, "y": 0.9},
    {"key": "w,a,s,d", "action": "joystick", "center_x": 0.15, "center_y": 0.8, "radius": 0.1},
    {"mouse": "move", "action": "drag", "sensitivity": 1.0, "dead_zone": 0.02}
  ]
}
```

Tervezett mezők: `dead_zone`, `sensitivity`, gamepad gomb → touch leképezés, profil
import/export JSON-ban.

## Amit ez a modul NEM fog csinálni

- **Nincs anti-cheat megkerülés.** Egyes játékok szabályzata korlátozhatja/tilthatja külső
  input-eszközök vagy keymapping használatát — ez a felhasználó felelőssége, a program nem
  rejti el vagy hamisítja az input-forrást.

## Fejlesztési sorrend (roadmap)

1. Motor: bindings betöltése, key/gamepad esemény → touch/tap parancs fordítás (nincs UI).
2. Profil import/export.
3. (P2, később) Vizuális keymap-szerkesztő.

**REAL DEVICE TEST REQUIRED**: a teljes keymapping-motor élesben csak valódi telefonnal és
valódi játékkal tesztelhető (latencia, pontosság, holt-zóna hangolás).
