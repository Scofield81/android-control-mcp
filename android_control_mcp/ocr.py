"""Opcionalis OCR-alapu fallback, amikor az uiautomator UI-hierarchia nem ad
hasznalhato elemeket (tipikusan: jatek, WebView, Canvas, egyedi rajzolt/Compose
felulet). Csak akkor aktiv, ha az `ocr` extra telepitve van
(`pip install -e ".[ocr]"`) ES a rendszeren tenylegesen elerheto a Tesseract
OCR motor binarisa - mindket hianyzo felteteltel vilagos, hasznalhato
hibauzenetet ad, nem hasal el ertelmezhetetlen kivetellel.

**NEM VALIDALVA VALODI KEPERNYON EBBEN A FEJLESZTESI MENETBEN** (nincs
csatlakoztatott eszkoz) - a logika helyes, de a Tesseract tenyleges
felismeresi minosege eszkoz-/nyelvfuggo.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OcrTextBox:
    text: str
    center: tuple[int, int]
    bounds: tuple[int, int, int, int]
    confidence: float


def ocr_available() -> tuple[bool, str]:
    """(elerheto, uzenet) - uzenet csak akkor van kitoltve, ha NEM elerheto,
    es megmondja, mit kell tenni."""
    try:
        import pytesseract
        from PIL import Image  # noqa: F401
    except ImportError:
        return False, (
            "Az OCR-fallback nincs telepitve. Telepitsd: pip install -e \".[ocr]\" "
            "(a projekt konyvtaraban), majd gyozodj meg rola, hogy a Tesseract OCR "
            "motor rendszerszinten is telepitve van (Windows: 'winget install "
            "UB-Mannheim.TesseractOCR'; Linux: 'sudo apt install tesseract-ocr')."
        )

    import pytesseract
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        return False, (
            "A pytesseract Python csomag telepitve van, de a Tesseract OCR motor "
            "binarisa nem talalhato a rendszeren. Windows: 'winget install "
            "UB-Mannheim.TesseractOCR', majd add hozza a PATH-hoz, vagy allitsd be "
            "'pytesseract.pytesseract.tesseract_cmd'-et."
        )
    return True, ""


def run_ocr(png_bytes: bytes, lang: str = "eng") -> list[OcrTextBox]:
    """Kepernyokep (PNG bajtok) OCR-elemzese, szoveges dobozok listajaval.

    lang: Tesseract nyelvkod (pl. 'eng', 'hun', 'eng+hun' tobb nyelvhez -
    az adott nyelv Tesseract adatfajljanak telepitve kell lennie).
    """
    import io

    import pytesseract
    from PIL import Image

    image = Image.open(io.BytesIO(png_bytes))
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)

    boxes: list[OcrTextBox] = []
    n = len(data.get("text", []))
    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError):
            conf = -1.0
        if conf < 30:  # alacsony bizalmu talalatok kiszurese (zaj)
            continue

        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        boxes.append(OcrTextBox(
            text=text,
            center=(x + w // 2, y + h // 2),
            bounds=(x, y, x + w, y + h),
            confidence=conf,
        ))

    return boxes


def format_ocr_box(box: OcrTextBox) -> str:
    return f"\"{box.text}\" center={box.center} conf={box.confidence:.0f}%"
