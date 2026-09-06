# Tool-katalógus (71 tool)

Automatikusan a tényleges regisztrált tool-okból és a forráskódban ténylegesen
előforduló `require_mode()`-hívásokból generálva — nem kézzel írt, ezért nem térhet
el a valós viselkedéstől. Mindig aktuális lista: `android-control-mcp --list-tools`.

**Mód-oszlop**: a `require_mode()` által ténylegesen megkövetelt minimum mód
(SAFE/NORMAL/ADMIN) — lásd [SECURITY_MODEL.md](SECURITY_MODEL.md). A `SAFE` NEM azt
jelenti, hogy a hívás soha nem változtat állapotot (pl. `connect_wifi` mód-kapu
nélküli, de kapcsolatot létesít) — ezt az „állapot-változó” oszlop jelzi külön.


## Eszköz / állapot

| Tool | Cél | Mód | Read-only / állapot-változó | ADB szükséges | Rescue/normál |
|---|---|---|---|---|---|
| `battery_status` | Akkumulator toltottsege, allapota (tolt/lemerul), homerseklete | SAFE | read-only | igen | normál |
| `device_info` | Az eszkoz alap adatai: gyarto, modell, Android verzio, SDK szint, build | SAFE | read-only | igen | normál |
| `device_list` | Csatlakoztatott Android eszkozok listaja (USB vagy 'adb connect' wifi) | SAFE | read-only | igen | normál |
| `network_status` | Halozati allapot: wifi SSID (ha lekerdezheto), IP cim, mobil adat allapota | SAFE | read-only | igen | normál |
| `screen_state` | A kepernyo aktualis allapota: be/kikapcsolva, es hogy zarolva van-e | SAFE | read-only | igen | normál |
| `set_mode` | A szerver engedely-modjanak valtasa futas kozben: 'safe', 'normal' vagy 'admin' | SAFE | állapot-változó | nem | normál |
| `storage_usage` | Belso tarhely-hasznalat (df /data, /sdcard) | SAFE | read-only | igen | normál |

## Képernyő / „látás”

| Tool | Cél | Mód | Read-only / állapot-változó | ADB szükséges | Rescue/normál |
|---|---|---|---|---|---|
| `observe_screen` | Egyetlen hivassal osszegyujti a kepernyo aktualis allapotat | SAFE | read-only | igen | normál |
| `ocr_screen` | OCR-alapu szovegfelismeres a kepernyon - fallback, amikor az 'ui_dump' | SAFE | read-only | igen | normál |
| `screen_record` | Rovid (max 30 mp) kepernyofelvetel keszitese MP4 formatumban | SAFE | read-only | igen | normál |
| `screenshot` | Kepernyokep keszitese az eszkozrol, PNG kepkent visszaadva | SAFE | read-only | igen | normál |
| `ui_dump` | Az aktualis kepernyo UI-elemeinek strukturalt listaja (uiautomator) | SAFE | read-only | igen | normál |
| `wait_for_text` | Var, amig egy adott szoveg megjelenik a kepernyon (ui_dump-ot ismetel) | SAFE | read-only | igen | normál |

## Szemantikus UI-vezérlés

| Tool | Cél | Mód | Read-only / állapot-változó | ADB szükséges | Rescue/normál |
|---|---|---|---|---|---|
| `find_element` | UI-elemek keresese szoveg/tartalom-leiras, resource-id es/vagy osztaly | SAFE | read-only | igen | normál |
| `scroll_to` | Lefele gorget, amig a keresett szoveg meg nem jelenik a kepernyon | NORMAL | állapot-változó | igen | normál |
| `tap_element` | Koppintas egy UI-elemre szoveg/resource-id/osztaly alapjan (kereses+koppintas | NORMAL | állapot-változó | igen | normál |
| `type_into` | Szoveg beirasa egy adott mezobe: megkeresi, ra koppint (fokuszalja), | NORMAL | állapot-változó | igen | normál |
| `wait_for_element` | Var, amig egy adott elem (szoveg es/vagy resource-id alapjan) | SAFE | read-only | igen | normál |

## Bemenet / gesztusok

| Tool | Cél | Mód | Read-only / állapot-változó | ADB szükséges | Rescue/normál |
|---|---|---|---|---|---|
| `double_tap` | Dupla koppintas (x, y)-on - pl. kep nagyitasahoz/kicsinyitesehez | NORMAL | állapot-változó | igen | normál |
| `drag` | Huzas (drag) (x1,y1)-tol (x2,y2)-ig - hosszabb ideju swipe, hogy az UI | NORMAL | állapot-változó | igen | normál |
| `long_press` | Hosszan tartott nyomas (x, y)-on - pl. kontextusmenuhoz vagy elem kijeloleshez | NORMAL | állapot-változó | igen | normál |
| `paste_clipboard` | Szoveg masolasa az eszkoz vagolapjara ('cmd clipboard set-primary-clip') | NORMAL | állapot-változó | igen | normál |
| `press_key` | Hardver-/rendszerbillentyu lenyomasa | NORMAL | állapot-változó | igen | normál |
| `scroll` | Gorgetes a kepernyo kozepetol: 'up', 'down', 'left' vagy 'right' | NORMAL | állapot-változó | igen | normál |
| `swipe` | Csuszo mozdulat (x1,y1) -> (x2,y2) pontok kozott, duration_ms ideig | NORMAL | állapot-változó | igen | normál |
| `tap` | Koppintas a kepernyo (x, y) pixelkoordinatajan | NORMAL | állapot-változó | igen | normál |
| `type_text` | Szoveg begepelese az aktivan fokuszalt beviteli mezobe | NORMAL | állapot-változó | igen | normál |

## Alkalmazások

| Tool | Cél | Mód | Read-only / állapot-változó | ADB szükséges | Rescue/normál |
|---|---|---|---|---|---|
| `app_info` | Egy alkalmazas reszletei: verzio, telepites datuma, engedelyek osszefoglaloja | SAFE | read-only | igen | normál |
| `clear_app_data` | Egy alkalmazas osszes helyi adatanak torlese (mint 'Adatok torlese' a Beallitasokban) | ADMIN | állapot-változó | igen | normál |
| `install_apk` | APK telepitese a szamitogeprol az eszkozre (`adb install`) | ADMIN | állapot-változó | igen | normál |
| `launch_app` | Alkalmazas inditasa csomagnev alapjan (pl. 'com.android.settings') | NORMAL | állapot-változó | igen | normál |
| `list_apps` | Telepitett alkalmazasok csomagneveinek listaja | SAFE | read-only | igen | normál |
| `open_url` | URL megnyitasa az alapertelmezett alkalmazasban (bongeszo, terkep, YouTube, stb | NORMAL | állapot-változó | igen | normál |
| `stop_app` | Alkalmazas eroszakos leallitasa ('force-stop') - mint a Beallitasokban | NORMAL | állapot-változó | igen | normál |
| `uninstall_app` | Alkalmazas eltavolitasa a csomagneve alapjan. ADMIN modot igenyel, megerositest ker | ADMIN | állapot-változó | igen | normál |

## Fájlok

| Tool | Cél | Mód | Read-only / állapot-változó | ADB szükséges | Rescue/normál |
|---|---|---|---|---|---|
| `delete_path` | Fajl vagy konyvtar torlese az eszkozon. Megerositest ker (nem visszavonhato) | NORMAL | állapot-változó | igen | normál |
| `file_info` | Egy fajl/konyvtar metaadatai: meret, jogosultsag, modositas ideje | SAFE | read-only | igen | normál |
| `list_files` | Fajlok/konyvtarak listazasa az eszkozon egy adott utvonalon | SAFE | read-only | igen | normál |
| `make_dir` | Uj konyvtar letrehozasa az eszkozon | NORMAL | állapot-változó | igen | normál |
| `move_path` | Fajl/konyvtar athelyezese vagy atnevezese az eszkozon (helyben, nem a gepre) | NORMAL | állapot-változó | igen | normál |
| `pull_file` | Fajl letoltese az eszkozrol a szamitogepre (`adb pull`) | NORMAL | állapot-változó | igen | normál |
| `push_file` | Fajl feltoltese a szamitogeprol az eszkozre (`adb push`) | NORMAL | állapot-változó | igen | normál |
| `read_file` | Szoveges fajl tartalmanak kiolvasasa az eszkozrol (log, config, stb.) | SAFE | read-only | igen | normál |

## Rendszer-kapcsolók

| Tool | Cél | Mód | Read-only / állapot-változó | ADB szükséges | Rescue/normál |
|---|---|---|---|---|---|
| `airplane_mode_toggle` | Repulo uzemmod be- vagy kikapcsolasa | NORMAL | állapot-változó | igen | normál |
| `bluetooth_toggle` | Bluetooth be- vagy kikapcsolasa | NORMAL | állapot-változó | igen | normál |
| `foreground_app` | Az eppen elterben lathato alkalmazas es aktivitas neve | SAFE | read-only | igen | normál |
| `open_notification_panel` | Az ertesitesi/gyorsbeallitasok panel lehuzasa a kepernyo tetejerol | NORMAL | állapot-változó | igen | normál |
| `screen_orientation` | Kepernyo-forgatas: 'auto', 'portrait', 'landscape', 'landscape_reverse' | NORMAL | állapot-változó | igen | normál |
| `set_volume` | Hangero beallitasa. stream: 'music', 'ring', 'alarm', 'notification', 'call' | NORMAL | állapot-változó | igen | normál |
| `wifi_toggle` | Wifi be- vagy kikapcsolasa | NORMAL | állapot-változó | igen | normál |

## Workflow (összetett)

| Tool | Cél | Mód | Read-only / állapot-változó | ADB szükséges | Rescue/normál |
|---|---|---|---|---|---|
| `assert_text` | Ellenorzi, hogy egy szoveg lathato-e (vagy NEM lathato-e) a kepernyon | SAFE | read-only | igen | normál |
| `fill_form` | Tobb mezo kitoltese egy hivasban | NORMAL | állapot-változó | igen | normál |
| `open_app_and_wait` | Alkalmazas inditasa, es varakozas, amig tenylegesen az kerul elotterbe | NORMAL | állapot-változó | igen | normál |
| `wait_until_screen_changes` | Var, amig a kepernyo UI-tartalma erzekelhetoen valtozik (nem ugyanaz | SAFE | read-only | igen | normál |

## Rendszer

| Tool | Cél | Mód | Read-only / állapot-változó | ADB szükséges | Rescue/normál |
|---|---|---|---|---|---|
| `backup_apps_data` | Teljes ADB mentes keszitese az eszkozrol egy .ab fajlba a szamitogepen | ADMIN | állapot-változó | igen | normál |
| `connect_wifi` | Kapcsolodas vezetek nelkuli ADB-vel ('adb connect ip:port') | SAFE | állapot-változó | igen | normál |
| `disconnect_device` | Vezetek nelkuli ADB kapcsolat bontasa egy eszkozzel | SAFE | állapot-változó | igen | normál |
| `list_notifications` | Az eszkozon jelenleg aktiv ertesitesek osszefoglaloja (dumpsys notification) | SAFE | read-only | igen | normál |
| `logcat_tail` | Az utolso N sor a rendszernaplobol (logcat) - hibakereseshez | SAFE | read-only | igen | normál |
| `reboot` | Eszkoz ujrainditasa. mode: 'normal', 'recovery' vagy 'bootloader' | ADMIN | állapot-változó | igen | normál |
| `running_processes` | Aktualisan futo folyamatok listaja az eszkozon (ps -A rovidítve) | SAFE | read-only | igen | normál |
| `shell_run` | Tetszoleges shell parancs futtatasa az eszkozon ('adb shell') | ADMIN | állapot-változó | igen | normál |
| `wait` | Egyszeru varakozas - kepernyoatmenetek/betoltodesek kivarasahoz | SAFE | read-only | nem | normál |

## Rescue (törött kijelző)

| Tool | Cél | Mód | Read-only / állapot-változó | ADB szükséges | Rescue/normál |
|---|---|---|---|---|---|
| `device_capabilities` | Az eszkoz/gep helyreallitasi kepessegeinek diagnosztikaja | SAFE | read-only | opcionális | Rescue |
| `explain_capability` | Egy kepesseg-jelzo (pl. 'wired_video_output') emberi nyelvu magyarazata | SAFE | read-only | nem | Rescue |
| `rescue_list_sessions` | A jelenleg futó (vagy nemrég leállt) Rescue munkamenetek listája | SAFE | read-only | nem | Rescue |
| `rescue_probe` | Teljes helyreallitasi diagnosztika + emberi nyelvu ajanlas egyben | SAFE | read-only | opcionális | Rescue |
| `rescue_scrcpy_status` | A hivatalos scrcpy binaris allapota ezen a gepen (megtalalhato-e, verzio) | SAFE | read-only | nem | Rescue |
| `rescue_start_mirror` | Teljes kepernyo-tukrozes es -vezerles inditasa (a hivatalos scrcpy sajat | NORMAL | állapot-változó | igen | Rescue |
| `rescue_start_otg` | ADB nélküli, AOA-alapú billentyűzet/egér-vezérlés indítása ('scrcpy --otg') | NORMAL | állapot-változó | nem (AOA, nem ADB) | Rescue |
| `rescue_stop_session` | Egy futó Rescue munkamenet (tükrözés vagy OTG) leállítása PID alapján | SAFE | állapot-változó | nem | Rescue |

---

Lásd még: [SECURITY_MODEL.md](SECURITY_MODEL.md) (mód-kapu + kockázat-kapu részletei),
[CONFIGURATION.md](CONFIGURATION.md) (környezeti változók).
