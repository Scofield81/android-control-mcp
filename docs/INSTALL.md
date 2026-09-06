# Részletes telepítési útmutató

A fő [README](../README.md) a legrövidebb, "van már SSH kulcsom" útvonalat írja le. Ez az
oldal azoknak szól, akiknek ez nem működött, vagy nem tudják, mi az az SSH kulcs / ADB.

## 1. A gép előkészítése

```bash
python3 --version    # 3.10+ szükséges
git --version
adb version           # ha "command not found", lásd a 3. pontot
```

## 2. A kód letöltése (klónozás)

A repó nyilvánosan olvasható, tehát HTTPS-en jelszó/token nélkül is klónozható:

```bash
git clone https://github.com/Scofield81/android-control-mcp.git
cd android-control-mcp
```

Ha SSH kulcsot szeretnél használni helyette (pl. mert gyakran dolgozol GitHub-bal):

```bash
ssh-keygen -t ed25519 -C "a-sajat-emailcimed@pelda.hu"
cat ~/.ssh/id_ed25519.pub
```

A kiírt sort másold be ide: **github.com → profilkép → Settings → SSH and GPG keys → New SSH
key**. Utána:

```bash
git clone git@github.com:Scofield81/android-control-mcp.git
cd android-control-mcp
```

## 3. ADB telepítése

**Windows:** `winget install Google.PlatformTools`, vagy töltsd le kézzel az
[Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools)
csomagot, és csomagold ki egy mappába, amit felveszel a `PATH`-ba (vagy add meg közvetlenül
az `ANDROID_CONTROL_ADB_PATH` környezeti változóban az `adb.exe` teljes útvonalát).

**macOS:** `brew install android-platform-tools`

**Linux (Ubuntu/Debian):** `sudo apt install android-tools-adb`

Ellenőrzés: `adb version` kiírja a verziószámot.

## 4. A telefon/tablet előkészítése

1. **Beállítások → A telefonról → Szoftver-információ** (gyártótól függően eltérő menüpont).
2. Koppints **7-szer** a **Buildszám**ra, amíg megjelenik: "Már fejlesztő vagy!".
3. **Beállítások → Rendszer → Fejlesztői beállítások** (vagy egyenesen a Beállítások
   tetején/alján), és kapcsold be az **USB hibakeresés**t.
4. Csatlakoztasd a telefont USB-kábellel a géphez. A telefon kijelzőjén megjelenik egy
   párbeszédablak: **"USB hibakeresés engedélyezése ezen a számítógépen?"** — pipáld be
   "Mindig engedélyezés ettől a számítógéptől", majd koppints **Engedélyezem**-re.
5. Ellenőrzés:

   ```bash
   adb devices
   ```

   A telefonodnak `device` állapottal kell megjelennie (nem `unauthorized`, nem `offline`).

> **Törött kijelzős telefon:** ha a képernyő nem használható, a fenti 4. lépést (a
> jóváhagyó gombra koppintás) **nem lehet elvégezni** — ez nem ennek a szoftvernek a
> korlátja, hanem az Android szándékos biztonsági mechanizmusa. Ha a telefon **korábban,
> még ép kijelzővel már jóváhagyta** ugyanezt a számítógépet, az engedély megmarad, és az
> ADB a törött kijelző ellenére is működik.

## 5. Python-környezet és a program telepítése

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Ellenőrzés:

```bash
android-control-mcp --list-tools
android-control-mcp --devices
```

## Hibaelhárítás

| Hiba | Megoldás |
|---|---|
| `adb: command not found` | Az Android SDK Platform-Tools nincs telepítve, vagy nincs a PATH-ban — lásd a 3. lépést. |
| `adb devices` üres listát ad | Csatlakoztasd a kábelt, ellenőrizd, hogy a kábel adatátvitelre is alkalmas (nem csak töltő), és hogy a telefonon a USB-mód "Fájlátvitel"-re van állítva. |
| `unauthorized` a `device_list` kimenetében | A telefon kijelzőjén jelenj meg a jóváhagyó párbeszédablaknak — koppints Engedélyezem-re. |
| `error: more than one device/emulator` | Add meg a `serial` paramétert (lásd `device_list`), vagy állítsd be az `ANDROID_CONTROL_DEFAULT_SERIAL`-t. |
| `git@github.com: Permission denied (publickey)` | Az SSH kulcsod nincs feltöltve a GitHub-fiókodhoz — használd inkább a HTTPS-es klónozást (2. lépés). |
