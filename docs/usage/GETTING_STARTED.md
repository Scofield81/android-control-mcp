# Első lépések

Feltételezi, hogy már [telepítve van](../installation/WINDOWS.md) a projekt.

## Futtatás

```bash
ANDROID_CONTROL_MODE=normal android-control-mcp
```

HTTP transzporttal (pl. teszteléshez, nem-stdio klienshez):

```bash
ANDROID_CONTROL_TRANSPORT=http ANDROID_CONTROL_PORT=8001 android-control-mcp
```

## `doctor` — diagnosztika

```bash
android-control-mcp doctor
```

Ellenőrzi: OS, Python-verzió, a projekt verziója, ADB elérhetőség/verzió, scrcpy
elérhetőség/verzió, config-fájl helye, MCP-szerver betölthetősége, regisztrált tool-ok
száma, csatlakoztatott eszközök és ADB-engedélyezettségi állapotuk (Wi-Fi vs USB
megkülönböztetve, ahol ez megbízhatóan eldönthető).

Gépi feldolgozáshoz (pl. AI-agentnek):

```bash
android-control-mcp doctor --json
```

Ha nincs csatlakoztatott telefon, ez **nem hiba** — a "Devices" sor `NO DEVICE CONNECTED`-et
mutat, az `Overall` státusz ettől még lehet `READY`.

## `configure` — MCP kliens beállítása

```bash
android-control-mcp configure
```

Interaktívan megkérdezi, melyik klienshez konfiguráljon (VS Code / Claude Code / Generic) —
részletek: [MCP_CLIENTS.md](MCP_CLIENTS.md).

## Első hívások

```
device_list
device_info
screenshot
ui_dump
```

Lásd a teljes [tool-katalógust](../reference/TOOLS.md), vagy futtasd:

```bash
android-control-mcp --list-tools
```
