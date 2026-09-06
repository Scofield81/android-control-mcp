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
| Google | Pixel 8 / 8 Pro / 8a | ✅ támogatott (Android 14 QPR2+) | Google hivatalos funkció-bevezetés, sajtóval megerősítve (androidauthority.com/androidpolice.com, 2024-06) |
| Google | Pixel 9 (összes) | ✅ támogatott | Google hivatalos funkció-bevezetés, sajtóval megerősítve (2024-06) |
| Samsung | Galaxy S8–S26, Note 8/9/10/20, Z Fold (összes), A90 5G, Tab S4–S11 | ✅ támogatott (DeX, vezetékes) | [Samsung hivatalos DeX GYIK](https://www.samsung.com/us/support/answer/ANS10001972/) |
| Samsung | Galaxy Z Flip7/8 (nem FE) | ✅ támogatott (DeX) | Samsung hivatalos DeX GYIK, ugyanaz mint fent |
| Samsung | Galaxy Z Flip7 FE és korábbi Flip modellek | ❌ nem támogatott (DeX) | Samsung hivatalos DeX GYIK — explicit kizárva |
| Samsung | Galaxy Tab S9 FE / S9 FE+ / S10 FE / S10 FE+ / S10 Lite | ❌ nem támogatott (HDMI-kimenet) | Samsung hivatalos DeX GYIK — explicit kizárva |
| Xiaomi | 15 | ✅ támogatott (vezetékes videó) | [Xiaomi hivatalos GYIK (KA-544001)](https://www.mi.com/global/support/faq/details/KA-544001/) |
| Xiaomi | 15T | ❌ nem támogatott (OTG igen, videó nem) | [Xiaomi hivatalos GYIK (KA-607966)](https://www.mi.com/global/support/faq/details/KA-607966/) |
| Xiaomi | POCO X7 / X7 Pro | ❌ nem támogatott (OTG igen, videó nem) | [Xiaomi hivatalos GYIK (KA-524823 / KA-528066)](https://www.mi.com/global/support/faq/details/KA-524823/) |
| Xiaomi | Redmi Note 12 | ❌ nem támogatott (DP/HDMI) | [Xiaomi hivatalos GYIK (KA-564504)](https://www.mi.com/global/support/faq/details/KA-564504/) — a közvetlen oldal-lekérdezés bot-védelem miatt 403-at adott, a forrás a keresőmotor indexén és az URL/KA-minta egyezésén alapul; lásd a `devices.json` `note` mezőjét |

**Átláthatósági megjegyzés**: minden fenti bejegyzés a gyártó saját hivatalos dokumentációjára
hivatkozik (nem sajtóoldalra vagy community/scrcpy jelentésre) — a pontos forrás-URL-eket lásd
az `android_control_mcp/rescue/data/devices.json` `source` mezőiben. Mielőtt éles döntést
hoznál egy adott telefonról, mindenképp ellenőrizd a gyártó saját, aktuális dokumentációját —
ezek a listák (főleg a Samsung DeX-kompatibilitás) modellenként és szoftververziónként
változhatnak.

## Bővítés

Új bejegyzés hozzáadásához szerkeszd az `android_control_mcp/rescue/data/devices.json`
fájlt. Kötelező mezők: `manufacturer`, `model_pattern` (regex), és legalább egy
`source` + `verified_date`. Ha nincs megbízható forrásod egy értékhez, hagyd `"unknown"`-on
— ne találj ki adatot.
