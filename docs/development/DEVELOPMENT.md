# Fejlesztői útmutató

## Fejlesztői telepítés

```bash
git clone git@github.com:Scofield81/android-control-mcp.git
cd android-control-mcp
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Tesztelés

```bash
python -m py_compile $(git ls-files '*.py')
pytest tests/ -v
ruff check .
```

A `tests/` alatt automatikus tesztek vannak (mind zöld, ADB/eszköz/scrcpy nélkül
futtatható, és a gép tényleges állapotától is izoláltan — lásd alább) — UI-dump parszolás,
csomagnév/keyevent-validáció, a mód-kapu logikája (a `set_mode` javított ceiling-viselkedésére
a tényleges regisztrált tool-on keresztül), OCR graceful-fallback, a kompatibilitási
adatbázis (`unknown`-alapértelmezés helyessége), a Rescue kapacitás-felismerés (mock
ADB-válaszokkal: `usb_host` a valódi `pm list features` kimenetből, nem az ADB-kapcsolat
puszta létéből derül ki), és a scrcpy-session indítási health-check (valódi, rövid életű
alfolyamatokkal: egy gyorsan kilépő folyamat NEM regisztrálódhat sikeres sessionként).

**Fontos teszt-elv** (2026-09-06-i valós eszközös teszt során derült ki): a tesztek NEM
támaszkodhatnak a futtató gép tényleges állapotára (van-e ADB-eszköz csatlakoztatva, van-e
scrcpy telepítve) — mindent explicit mock-kal kell izolálni, különben a teszt hamisan
elbukik (vagy hamisan sikeres) attól függően, mi fut éppen a fejlesztő gépén.

**Nincs GitHub Actions CI** — a tesztelés helyben történik, `pytest tests/ -v`-vel, tudatos
projektdöntés alapján (lásd [CONTRIBUTING.md](../../CONTRIBUTING.md)).

## Kódstruktúra

```
android_control_mcp/
  __main__.py       - CLI belépési pont (--list-tools, --devices, doctor, configure)
  server.py         - FastMCP szerver + tool-regisztráció
  config.py         - AppConfig, Mode enum, env/config.json betöltés
  permissions.py    - require_mode(), ask_permission()
  adb.py            - ADB alfolyamat-hívások, list_devices(), run_shell()
  doctor.py          - 'doctor' diagnosztikai parancs
  cli_configure.py   - 'configure' MCP kliens-konfigurator
  tools/             - egy fájl kategóriánként, @mcp.tool() dekorátorral
  rescue/             - Rescue mód: capabilities.py, session.py, scrcpy_binary.py, compat_db.py
```

## Fejlesztési elvek

- **ADB kizárólag `asyncio.create_subprocess_exec`-en keresztül** — nincs ADB-kliens
  Python-függőség, minimális lábnyom, könnyű debug.
- **scrcpy a hivatalos, telepített binárison keresztül alfolyamatként** — nincs saját,
  újraimplementált videó/vezérlő-protokoll (lásd [usage/MIRRORING.md](../usage/MIRRORING.md)).
- **Minden shell-stringbe kerülő dinamikus paraméter idézett/validált** — lásd
  [reference/SECURITY_MODEL.md](../reference/SECURITY_MODEL.md).
- **Sose találj ki támogatást** — a Rescue kapacitás-jelentés minden mezője
  `supported`/`unsupported`/`unknown`, sosem `unknown` helyett feltételezés.

## Hozzájárulás

A projekt forráskód-elérhető (source-available), nem klasszikus nyílt forráskódú — lásd
[CONTRIBUTING.md](../../CONTRIBUTING.md) és [LICENSE](../../LICENSE).
