# Integráció voice/agent/saját rendszerekkel

Ez az oldal **nem egyetlen konkrét projektre** van írva — azt magyarázza el, hogyan
építhető az Android Control MCP egy tetszőleges hangvezérelt asszisztens, desktop AI, saját
agent, JARVIS-szerű rendszer, otthon-automatizálási megoldás vagy saját LLM-alkalmazás mögé.

## Architektúra

```
Felhasználó (hang vagy szöveg)
        │
        ▼
Voice/UI frontend  (STT, chat UI, wake-word rendszer stb. — NEM ennek a projektnek a része)
        │
        ▼
LLM / Agent  (intent-felismerés, tool selection — pl. Claude, GPT, saját LLM)
        │
        ▼
Android Control MCP  (ez a projekt — MCP szerver, 71 tool)
        │
        ▼
Android telefon (ADB / scrcpy / AOA)
```

Példa: a felhasználó azt mondja: *"Nyisd meg a WhatsAppot."* → a voice frontend
szöveggé alakítja → az LLM/agent felismeri az intentet, kiválasztja a `launch_app` tool-t a
megfelelő csomagnévvel → az Android Control MCP végrehajtja → az eredmény visszajut a
felhasználóhoz (hang vagy szöveg formájában, a frontend feladata).

## Az integráció öt lépése

1. **Intent-felismerés** — a frontend/LLM eldönti, mit szeretne a felhasználó (ez NEM ennek
   a projektnek a feladata).
2. **MCP tool selection** — az agent kiválasztja a megfelelő tool-t és paramétereket (lásd
   [reference/TOOLS.md](../reference/TOOLS.md) a teljes katalógusért, kategorizálva).
3. **Permission/confirmation** — lásd lent, "Biztonsági elv".
4. **Végrehajtás** — az Android Control MCP a tényleges ADB/scrcpy-műveletet elvégzi.
5. **Eredmény-visszajelzés** — a tool szöveges (esetenként kép-) választ ad vissza, amit a
   frontend alakít hangra/UI-ra.

## Biztonsági elv: destruktív műveletnél user-confirmation kötelező

A szerver saját [kockázat-kapuja](../reference/SECURITY_MODEL.md) (`ask_permission`) MCP
elicit-en keresztül kér megerősítést — ha a kliens NEM támogatja az elicitet, az integráló
rendszernek **saját magának** kell egy ezzel egyenértékű megerősítést beépítenie, mielőtt
egy destruktív tool-t (pl. `uninstall_app`, `delete_path`, `clear_app_data`, `shell_run`,
`reboot`) meghívna:

```
Felhasználó:  "Töröld a Facebook alkalmazást."
Agent:        "Biztosan törlöm a Facebook alkalmazást és az adatait? (igen/nem)"
Felhasználó:  "Igen."
Agent:        → uninstall_app(package="com.facebook.katana")
```

**Ez alkalmazásszintű user-confirmation, NEM lockscreen bypass és NEM security bypass** — a
saját eszközén, a saját akaratából működő felhasználó explicit jóváhagyása egy amúgy is
elérhető műveletről.

Ha `ANDROID_CONTROL_AUTO_APPROVE=1` van beállítva a szerveren (csak zárt, megbízható
környezetben ajánlott), a szerver saját kockázat-kapuja automatikusan jóváhagy — ez esetben
**az integráló rendszer felelőssége** a fenti visszakérdezés-minta beépítése, mert a szerver
maga nem fog rákérdezni.

## Csatlakozási módok

- **stdio** (alap) — helyi folyamatként indított agent/desktop-alkalmazás esetén a
  legegyszerűbb.
- **HTTP** (`ANDROID_CONTROL_TRANSPORT=http`) — ha a voice/agent-rendszer külön
  folyamatban/konténerben fut, és hálózaton (csak `127.0.0.1`-en, lásd
  [reference/CONFIGURATION.md](../reference/CONFIGURATION.md)) éri el az MCP szervert.

## Nem cél most

Ez a dokumentum **nem** ír le egy konkrét, kész voice assistant implementációt — a cél egy
tiszta, dokumentált MCP-felület és integrációs minta, amit bármilyen külső rendszer
felhasználhat. Teljes voice-frontend/wake-word-rendszer implementálása jelenleg nem része a
projektnek.
