# Biztonsági szabályzat

## Támogatott verziók

A projekt jelenleg `0.x.x` fejlesztési állapotban van (valós hardveres validáció alatt) —
mindig a legfrissebb `main` ág kap biztonsági javítást.

## Sérülékenység bejelentése

**Kérjük, NE nyiss publikus GitHub Issue-t** biztonsági sérülékenységhez (exploit, konkrét
megkerülési technika, kihasználható hiba részletei) — ez a nyilvánosság előtt tenné közzé,
mielőtt javítás készülne.

Ehelyett írj közvetlenül: **admin@zsebai.hu**

A jelentésben, ha lehetséges, add meg:

- a projekt verzióját/commit hash-ét;
- a pontos reprodukciós lépéseket;
- a lehetséges hatást (mit tud elérni egy támadó);
- (ha van) javasolt javítást.

## Responsible disclosure

- A bejelentést lehetőség szerint 7 napon belül visszaigazoljuk.
- A javítás elkészültéig kérjük, ne hozd nyilvánosságra a részleteket.
- A javítás kiadása után — veled egyeztetve — hitelt adunk a felfedezésért, ha ezt szeretnéd.

## Ami NEM biztonsági sérülékenység-bejelentés témája

Ez a projekt **szándékosan** nem implementál és nem is fog implementálni
lockscreen-bypass-t, PIN/minta brute force-t, exploitot vagy titkosítás-megkerülést — lásd a
[LICENSE](LICENSE) 6. pontját és a README "Fontos határ" szakaszát. Az ilyen irányú
"funkció-kérést" nem biztonsági sérülékenységként, hanem a projekt szándékos, dokumentált
határaként kezeljük — ezek nem fogadhatók el, függetlenül a bejelentés csatornájától.

## Mit tekintünk valódi biztonsági problémának

Például: shell injection egy tool-paraméteren keresztül, a mód-kapu (SAFE/NORMAL/ADMIN)
megkerülése kódszinten, a kockázat-kapu (`ask_permission`) megkerülhetősége, credential-
szivárgás naplóba/hibaüzenetbe, vagy bármi, ami a dokumentált engedély-modellt
(lásd [docs/reference/SECURITY_MODEL.md](docs/reference/SECURITY_MODEL.md)) ténylegesen
megkerüli.
