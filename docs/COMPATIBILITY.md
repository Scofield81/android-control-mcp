# Kompatibilitás — platform-tények és gyártói adatbázis

## Alapelv: `supported` / `unsupported` / `unknown`

A `device_capabilities`/`rescue_probe` tool-ok **soha** nem találnak ki támogatást. Ha egy
képességet nem tudunk megbízhatóan megállapítani (sem ADB-lekérdezésből, sem a
gyártó/modell-adatbázisból), az érték `unknown` — ez **egyenrangú, valid válasz**, nem hiba.

**Konkrétan: pusztán abból, hogy egy telefonnak USB-C csatlakozója van, NEM következik, hogy
DisplayPort Alt Mode-ot (vezetékes videó-kimenetet) is támogat.** Ez a leggyakoribb hibás
feltételezés — sok modern USB-C telefon **csak** töltésre/adatátvitelre képes az USB-C-n,
videóra nem.

## Android platform-minimumok (verzió-alapú tények)

| Funkció | Minimum Android verzió | Megjegyzés |
|---|---|---|
| USB Host API | 3.1 (API 12) | Hardverfüggő, hogy a konkrét eszköz ezt ki is szereli-e. |
| AOAv2 (Accessory HID) | 4.1 (API 16) | Hardver-/OEM accessory-mode függő. |
| `scrcpy` tükrözés | 5.0 (API 21) | **ADB engedélyezés/authorization szükséges** — ez torott/nem látható kijelzőnél éppen az a lépés, ami tipikusan nem pótolható utólag. |
| `scrcpy` audio | 11 (API 30) | |
| `scrcpy --otg` (AOA vezérlés) | — | Nem igényel ADB-t, de **nincs videó és nincs audio**. |
| Vezetékes videó-kimenet (DP Alt Mode) | — | **Ez NEM Android-verzió kérdése, hanem konkrét hardver/modell képesség.** |

## Két különböző dolog: USB OTG/Host és AOA2/scrcpy OTG

- **USB OTG / USB Host**: a telefon képes-e USB-perifériákat (billentyűzet, egér, pendrive)
  *fogadni* — ez egy általános Android-platform képesség.
- **AOAv2 / `scrcpy --otg`**: ennek egy specifikus alkalmazása, ahol a **számítógép** adja ki
  magát perifériának (billentyűzet/egér) a telefon felé — ehhez a telefonnak accessory-mode
  támogatása kell, ami hardver-/OEM-függő, és PC-oldalról közvetlenül nem lekérdezhető anélkül,
  hogy ténylegesen megpróbálnánk csatlakozni (ezért marad `unknown`, amíg a `rescue_start_otg`
  ténylegesen ki nem próbálja).

## Gyártói/modell adatbázis (`android_control_mcp/rescue/data/devices.json`)

Kis, szándékosan konzervatív, bővíthető JSON. Minden bejegyzéshez **forrás** és
**ellenőrzés dátuma** tartozik. Jelenlegi bejegyzések:

| Gyártó | Modell(ek) | Vezetékes videó | Forrás |
|---|---|---|---|
| Google | Pixel 8 / 8 Pro / 8a | ✅ támogatott (Android 14 QPR2+) | Google hivatalos bejelentés, 2024-06 |
| Google | Pixel 9 (összes) | ✅ támogatott | Google hivatalos bejelentés, 2024-06 |
| Samsung | Galaxy S8–S23, Note 8–20 | ✅ támogatott (DeX) | Samsung DeX dokumentáció — *community/scrcpy jelentések, ebben a menetben nem egyenként újra-ellenőrizve* |
| Xiaomi | 15 | ✅ támogatott | *community/scrcpy jelentés, nem független forrásból ellenőrizve* |
| Xiaomi | 15T, POCO X7 | ❌ nem támogatott (OTG igen, videó nem) | *community/scrcpy jelentés* |
| Xiaomi | Redmi Note 12 | ❌ nem támogatott | *community/scrcpy jelentés* |

**Fontos átláthatósági megjegyzés**: a Google Pixel-bejegyzéseket ebben a fejlesztési
menetben friss webes kereséssel ellenőriztük (2026-09-06). A Samsung/Xiaomi bejegyzések
korábbi (a felhasználó review-jában megadott) állítások — ezeket **nem** ellenőriztük
egyenként elsődleges forrásból ebben a menetben, ezért `source` mezőjük ezt explicit jelzi.
Mielőtt éles döntést hoznál egy adott telefonról, ellenőrizd a gyártó saját, aktuális
dokumentációját.

## Bővítés

Új bejegyzés hozzáadásához szerkeszd az `android_control_mcp/rescue/data/devices.json`
fájlt. Kötelező mezők: `manufacturer`, `model_pattern` (regex), és legalább egy
`source` + `verified_date`. Ha nincs megbízható forrásod egy értékhez, hagyd `"unknown"`-on
— ne találj ki adatot.
