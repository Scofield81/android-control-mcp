# Linux telepítés

> **⚠️ NOT YET VALIDATED ON REAL LINUX INSTALLATION.**
> A projekt kódja platformfüggetlenül van megírva (tisztán a szabványos `adb` binárisra és a
> Python standard library-ra épül, nincs Windows-specifikus kód a fő logikában), és a lenti
> lépések a hivatalos csomagkezelők dokumentált parancsai — de ezt a telepítési utat **ebben
> a fejlesztési szakaszban még nem futtattam le ténylegesen egy valódi Linux gépen**. Amíg ez
> meg nem történik, ezt az oldalt **ne tekintsd tesztelt, garantált támogatásnak** — csak
> dokumentált, ésszerű útmutatónak.

A elsődleges, ténylegesen validált platform egyelőre a [Windows](WINDOWS.md).

## Függőségek

```bash
python3 --version   # 3.10+
```

**ADB** (hivatalos csomagkezelői útvonalak):

| Disztribúció | Parancs |
|---|---|
| Ubuntu/Debian | `sudo apt install android-tools-adb` |
| Fedora | `sudo dnf install android-tools` |
| Arch | `sudo pacman -S android-tools` |

**scrcpy** (opcionális — csak a képernyő-tükrözés/Rescue módhoz kell):

| Disztribúció | Parancs |
|---|---|
| Ubuntu/Debian (24.04+) | `sudo apt install scrcpy` |
| Fedora | `sudo dnf install scrcpy` |
| Arch | `sudo pacman -S scrcpy` |

Ha a disztribúciód csomagkezelőjében elavult verzió van, a
[hivatalos GitHub Release](https://github.com/Genymobile/scrcpy/releases) oldalról tölthető
a legfrissebb.

## Telepítés

```bash
git clone https://github.com/Scofield81/android-control-mcp.git
cd android-control-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

Ellenőrzés:

```bash
android-control-mcp doctor
```

Automatizált (`install_linux.sh` jellegű) telepítő szkript **még nincs** — ez a Windows-hoz
hasonló automatizálás roadmap-tétele, csak azután érdemes megírni, hogy a fenti kézi út
valós Linux gépen validálva lett. Addig a [MANUAL.md](MANUAL.md) lépéseit érdemes követni.

## Következő lépés

Telepítés után: [MCP kliens beállítása](../usage/MCP_CLIENTS.md).
