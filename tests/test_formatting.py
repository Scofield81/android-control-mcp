from __future__ import annotations

from android_control_mcp.formatting import human_bytes, parse_key_value_lines, truncate


def test_human_bytes_small():
    assert human_bytes(500) == "500 B"


def test_human_bytes_mb():
    assert human_bytes(5 * 1024 * 1024) == "5.0 MB"


def test_parse_key_value_lines():
    text = "level: 87\nscale: 100\nstatus: 2\n"
    data = parse_key_value_lines(text)
    assert data == {"level": "87", "scale": "100", "status": "2"}


def test_truncate_short_text_unchanged():
    assert truncate("hello", max_chars=100) == "hello"


def test_truncate_long_text_is_cut_with_marker():
    long_text = "x" * 100
    result = truncate(long_text, max_chars=10)
    assert result.startswith("x" * 10)
    assert "levagva" in result
