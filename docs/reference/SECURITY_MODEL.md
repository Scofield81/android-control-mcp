# Biztonsági/engedély-modell

## 1. réteg — mód-kapu

A szerver **egy** módban fut (`ANDROID_CONTROL_MODE`, lásd [CONFIGURATION.md](CONFIGURATION.md)) —
ez rögzíti a **felső határt** (`max_mode`) is: a `set_mode` tool ennél magasabbra soha nem
tud menni, de a rögzített határon belül szabadon oda-vissza kapcsolható (pl. egy
`admin`-nal indított szerveren `safe`→`normal`→`admin` bármelyik irányba).

| Mód | Mit enged |
|---|---|
| **SAFE** | csak olvasás: `device_info`, `screenshot`, `ui_dump`, `find_element`, `observe_screen`, `logcat_tail`, `list_apps`, fájlolvasás, stb. — lásd a teljes listát [TOOLS.md](TOOLS.md)-ban |
| **NORMAL** | a fentiek **+** koppintás/gépelés/gesztusok, alkalmazás indítása/leállítása, fájlműveletek (írás/törlés), rendszer-kapcsolók, workflow-tool-ok |
| **ADMIN** | a fentiek **+** `install_apk`, `uninstall_app`, `clear_app_data`, `reboot`, `backup_apps_data`, `shell_run` (tetszőleges parancs) |

## 2. réteg — kockázat-kapu (`ask_permission`)

A módtól függetlenül interaktív megerősítést kér minden visszafordíthatatlan/adatvesztéssel
járó művelet: alkalmazás eltávolítása, alkalmazás adatainak törlése, ismeretlen APK
telepítése, fájl/könyvtár törlése, bootloader/recovery újraindítás, tetszőleges shell
parancs.

Ha a kliens nem támogatja az elicitet: a művelet **elutasításra kerül**, hacsak az
`ANDROID_CONTROL_AUTO_APPROVE=1` nincs bekapcsolva (csak zárt, megbízható környezetben).

Minden művelet **auditálva** van (stderr + opcionális naplófájl, lásd
`ANDROID_CONTROL_AUDIT_LOG`).

## Shell injection védelem

Minden shell-stringbe kerülő dinamikus paraméter (fájlútvonal, csomagnév, keyevent-kód,
szöveg) **idézett** (`shlex.quote`) vagy **formailag validált** (pl. csomagnév regex),
mielőtt egy `adb shell` parancssorba interpolálódik. A `shell_run` tool szándékos kivétel:
az kifejezetten tetszőleges parancs futtatására való, ezért **ADMIN** módot és explicit
megerősítést igényel.

## Telepítő/installer-oldali biztonsági elvek

Az [install/uninstall/configure szkriptek](../installation/WINDOWS.md) betartják:

- **sosem** módosítanak Android-eszközt (nem kapcsolnak be ADB-t/USB-hibakeresést, nem
  fogadnak el RSA-authorizationt, nem küldenek inputot a telefonnak);
- **sosem** gyűjtenek személyes adatot, nem mentenek képernyőt/screenshotot;
- **sosem** naplóznak credentialt/titkos adatot;
- meglévő MCP-kliens config fájlt **sosem** írnak felül vakon — parse → biztonsági mentés →
  csak a saját bejegyzésük módosítása.

## A "Fontos határ" — mit NEM csinál ez a szoftver

Ez az eszköz **nem képes és nem is célja** képernyőzár vagy más hozzáférés-védelem
**jogosulatlan** megkerülése — sem PIN/minta próbálgatás (brute force), sem exploit, sem
titkosítás-megkerülés. Részletek: a README "Fontos határ" szakasza és
[usage/RESCUE.md](../usage/RESCUE.md) "A kemény korlát" szakasza.

## Voice/agent-integrációnál elvárt user-confirmation minta

Ha az Android Control MCP-t egy hangvezérelt/agent-alapú rendszer mögé teszed (lásd
[development/INTEGRATION.md](../development/INTEGRATION.md)), a **destruktív vagy érzékeny
műveletnél az integráló agentnek vissza kell kérdeznie** a felhasználótól (pl. "Biztosan
töröljem az alkalmazást?" → explicit "Igen"). Ez a szerver saját `ask_permission`
mechanizmusát egészíti ki egy alkalmazás-szintű megerősítéssel — **nem** lockscreen bypass
vagy security bypass, hanem normál user-confirmation minta.
