# Képernyő-tükrözés — architektúra

## Miért a hivatalos scrcpy binárist hívjuk, nem reimplementáljuk a protokollt

Egy korábbi verzió a `scrcpy-client` PyPI csomagot (leng-yue/py-scrcpy-client) próbálta
beépíteni önálló, AI-vezérelt gyors-koppintás backendként. Ezt **eltávolítottuk**, mert:

- utolsó PyPI kiadása 2022-ből való;
- a `scrcpy-server` **1.20** protokollverzióra épül, míg a hivatalos scrcpy már **4.x**
  sorozatnál jár — a protokoll azóta jelentősen változott;
- hivatalosan csak Python `>=3.7,<3.11`-et támogat;
- vannak Android 15 inkompatibilitási jelentések;
- és — ami a legfontosabb koncepcionális hiba volt — a scrcpy `--otg` módja **nem egy
  parancssorból hívható API egyedi érintés-parancsokhoz**: a felhasználó **saját, fizikai**
  billentyűzetét/egerét fogadja, amit az SDL-ablak (amit a scrcpy nyit) kapcsolgat AOA HID
  eseményekre. Ez emberi kezelésre való, nem programozott `tap(x, y)` hívásokra.

**Az AI-vezérelt automatizálás (`tap`, `swipe`, `ui_dump` stb.) ezért továbbra is tisztán
ADB-n keresztül megy** (`android_control_mcp/tools/common.py` `do_tap`/`do_swipe`) — ez
tipikusan 100-300 ms/művelet, de megbízható, jól tesztelt, és nem igényel semmilyen extra
függőséget.

A **Rescue mód** más célra való: **emberi** operátor nagy képernyős, kényelmes vezérlésére —
ehhez a hivatalos, aktívan karbantartott `scrcpy.exe`-t indítjuk alfolyamatként
(`android_control_mcp/rescue/session.py`), a saját ablakában. Nincs saját videó-dekóder, nincs
saját protokoll-implementáció — a scrcpy csinálja, amiben már bizonyítottan jó.

## Streaming profilok

| Profil | Cél | Kapcsolók |
|---|---|---|
| `quality` | maximális képminőség | `--video-bit-rate=16M --max-size=0` |
| `balanced` | alapértelmezett, jó kompromisszum | `--video-bit-rate=8M --max-size=1920` |
| `low_latency` | gyors reakció, kisebb kép | `--video-bit-rate=4M --max-size=1280 --max-fps=30` |
| `gaming` | nagy FPS, nagy felbontás | `--video-bit-rate=12M --max-size=1920 --max-fps=60` |

Ezek a scrcpy saját, dokumentált kapcsolói — a szerver csak összeállítja a parancssort, nem
állít elő konkrét mérési eredményt "mert jól hangzik". Ha egy adott kódek/felbontás az adott
telefonon nem támogatott, a scrcpy maga jelzi a hibát a saját kimenetén.

## Ablakkezelés (resize, fullscreen, rotation, high-DPI, multi-monitor, touch)

Ezt mind a **scrcpy saját ablaka** kezeli — nincs erre saját Windows Viewer-alkalmazás ebben
a verzióban. Ha a felhasználó Windows érintőképernyős gépet használ, a scrcpy ablaka saját
maga fogadja az egér/érintés-eseményeket az operációs rendszertől; ehhez nem kellett saját
koordináta-transzformációs réteget írnunk (letterboxing, DPI-skálázás, rotáció — mind a
scrcpy saját, bevált kódjában van kezelve).

**Jövőbeli terv (nincs implementálva)**: egy önálló `android-control-viewer` Windows
alkalmazás, ami beágyazottan (nem külön ablakban) jelenítené meg a scrcpy folyamot, saját
UI-elemekkel (pl. Rescue-specifikus gyorsgombok). Ehhez a scrcpy `--window-borderless` / SDL
ablak-embedding vagy a scrcpy saját, dokumentált beágyazási lehetőségeinek tanulmányozása
szükséges — ez **P2/P4-es, hardveres teszteléssel együtt validálandó** munka.
