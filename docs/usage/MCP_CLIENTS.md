# MCP kliens-konfiguráció

Az Android Control MCP **nem VS Code-kiegészítő és nem Claude Code-kiegészítő** — egy önálló,
helyben futó MCP szerver/runtime, amit **bármelyik** MCP-kompatibilis kliens elérhet:

```
Windows/Linux
    │
    ├── Android Control MCP  (Python runtime + ADB + scrcpy)
    │
    ├── Android telefon
    │
    └── MCP kliens (bármelyik):
          ├── VS Code
          ├── Claude Code
          ├── Generic/saját MCP kliens
          └── később: voice assistant / saját agent — lásd ../development/INTEGRATION.md
```

A Windows alatt megnyíló telefon-tükröző ablakot maga a scrcpy/Android Control rendszer
adja — függetlenül attól, hogy a tool-hívás VS Code-ból, Claude Code-ból vagy máshonnan jött.

## Automatizált beállítás

```bash
android-control-mcp configure
```

Interaktívan kérdez (kliens, majd scope), vagy szkriptelhetően:

```bash
android-control-mcp configure --client vscode --scope project
android-control-mcp configure --client claude-code --scope local
android-control-mcp configure --client generic
```

**Meglévő konfigurációt sosem ír felül vakon** — beolvassa, biztonsági mentést készít, és
csak a saját (`android-control`) bejegyzését módosítja/hozza létre.

## VS Code

A VS Code hivatalos MCP-konfigurációs modelljét használjuk
([code.visualstudio.com/docs/agents/reference/mcp-configuration](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)):

- **Project/workspace scope**: `.vscode/mcp.json` a repo/workspace gyökerében, `"servers"`
  kulcs alatt. Ezt a `configure --client vscode --scope project` automatikusan írja/frissíti
  (biztonsági mentéssel).
- **User scope**: a VS Code **user-szintű** MCP-konfigurációs fájljának pontos elérési útja
  **nincs stabilan dokumentálva** a VS Code hivatalos forrásaiban, ezért ezt szándékosan
  **nem** találjuk ki/írjuk automatikusan. Helyette: Command Palette → **"MCP: Open User
  Configuration"**, és a `configure --client vscode --scope user` kiírja a beillesztendő JSON
  blokkot.

Ellenőrzés: Command Palette → **"MCP: List Servers"**.

## Claude Code

A hivatalos `claude mcp add` CLI-t használjuk
([code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp)) — nem kézzel írt config
fájlt. A `configure --client claude-code --scope <local|project|user>` megkeresi a `claude`
CLI-t, és ha megtalálja, lefuttatja helyetted; ha nem, kiírja a pontos parancsot, amit te
futtathatsz:

```bash
claude mcp add --scope local --transport stdio --env ANDROID_CONTROL_MODE=normal \
  android-control -- <python-interpreter> -m android_control_mcp
```

Scope-ok: `local` (csak ez a projekt, alapértelmezett), `project` (megosztott `.mcp.json` a
repóban), `user` (minden projektedben elérhető).

Ellenőrzés:

```bash
claude mcp list
```

## Generic MCP kliens

Saját agent, voice assistant vagy más MCP-kompatibilis kliens esetén:

```bash
android-control-mcp configure --client generic
```

Ez egy **vendor-független** példa-config fájlt ír ki — a pontos kulcsnév/formátum a te
kliensedtől függ, ebből másold át a `command`/`args`/`env` mezőket. A szerver maga stdio
(vagy `ANDROID_CONTROL_TRANSPORT=http`-tal HTTP) transzporton beszél, ami a legtöbb MCP
klienssel kompatibilis.

## Manuális stdio-konfiguráció (bármelyik klienshez)

```json
{
  "command": "/abszolut/ut/.venv/bin/android-control-mcp",
  "env": {
    "ANDROID_CONTROL_MODE": "normal",
    "ANDROID_CONTROL_AUDIT_LOG": "~/.local/state/android-control-mcp/audit.log"
  }
}
```

Windows alatt a `command` a venv `Scripts\android-control-mcp.exe` útvonala (vagy `python.exe
-m android_control_mcp`, ha nincs telepítve konzol-szkriptként).
