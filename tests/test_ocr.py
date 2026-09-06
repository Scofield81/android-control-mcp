"""Tesztek az opcionalis OCR-fallback graceful-degradation viselkedesehez.

A tesztkornyezetben nincs telepitve sem 'pytesseract', sem a Tesseract
binaris - ez pontosan a leggyakoribb (telepites nelkuli) allapotot
tesztelik: ilyenkor 'ocr_available()' False-t es egy hasznalhato,
telepitesi utmutatot tartalmazo uzenetet ad, SOHA nem dob kivetelt."""

from __future__ import annotations

from android_control_mcp.ocr import ocr_available


def test_ocr_available_false_without_dependencies():
    available, message = ocr_available()
    assert available is False
    assert "ocr" in message.lower() or "tesseract" in message.lower()
    assert message  # nem ures - konkret utmutatast ad
