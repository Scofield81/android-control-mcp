# Hozzájárulás az Android Control MCP fejlesztéséhez

Jelenleg hibajelentéseket és funkciójavaslatokat várunk a GitHub Issues felületén. A licenc
(lásd [`LICENSE`](LICENSE)) nem engedélyezi a módosított változatok szabad terjesztését, ezért
kód-hozzájárulásokat és pull requesteket jelenleg nem fogadunk.

Ha hibát találtál, vagy ötleted van egy új tool-hoz/funkcióhoz, nyiss egy issue-t a megfelelő
[Issue Form sablonnal](.github/ISSUE_TEMPLATE/):

- **[Hibajelentés](../../issues/new?template=bug_report.yml)** — mit próbáltál csinálni
  (melyik tool, milyen paraméterekkel), mi történt, mit vártál volna helyette, az eszköz
  gyártója/modellje és Android verziója, releváns `ANDROID_CONTROL_MODE`/`stderr`-hiba.
- **[Funkciójavaslat](../../issues/new?template=feature_request.yml)** — milyen problémát
  oldana meg, van-e elképzelésed a konkrét tool-névről/paraméterekről.
- **[Eszköz-kompatibilitási bejelentés](../../issues/new?template=device_compatibility.yml)** —
  ha kipróbáltad a Rescue módot egy telefonon; ez **nem** válik automatikusan hivatalos
  `supported` bejegyzéssé a kompatibilitási adatbázisban, előbb ellenőrizzük (lehetőleg a
  gyártó hivatalos dokumentációjával összevetve).

## Pull request folyamat

A licenc (lásd [`LICENSE`](LICENSE)) nem engedélyezi a módosított változatok szabad
terjesztését, ezért **kód-hozzájárulásokat és pull requesteket jelenleg nem fogadunk el**.
Ha van egy konkrét javításod, nyiss inkább egy issue-t a leírással — a döntés a
karbantartóé marad, hogy beépíti-e.

## Tesztelési elvárások (ha mégis kódot javasolsz egy issue-ban)

- `pytest tests/ -v` teljes suite zöld legyen.
- Új logika esetén célzott teszt tartozzon hozzá.
- A teszteknek a futtató gép **tényleges** állapotától (van-e csatlakoztatott ADB-eszköz,
  telepítve van-e scrcpy) függetlennek kell lenniük — mindent explicit mock-kal kell
  izolálni, lásd [docs/development/DEVELOPMENT.md](docs/development/DEVELOPMENT.md).
- `ruff check .` és `python -m py_compile` hibamentes legyen.
- **Nincs GitHub Actions CI** ebben a projektben — a tesztelés helyben történik.

**Nem fogadunk el** olyan javaslatot vagy kódot, amely képernyőzár/hozzáférés-védelem
jogosulatlan megkerülésére irányul — lásd a [LICENSE](LICENSE) 6. pontját.
