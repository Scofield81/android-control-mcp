"""Tesztek a common.py tiszta (nem-adb-fuggo) logikajahoz: UI-dump parszolas,
elem-kereses, csomagnev/keyevent validacio, shell-idezes."""

from __future__ import annotations

import pytest

from android_control_mcp.tools.common import (
    find_matching_elements,
    format_element,
    parse_ui_elements,
    sh_quote,
    validate_keycode,
    validate_package_name,
)

SAMPLE_XML = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.example"
        content-desc="" clickable="false" enabled="true" selected="false" bounds="[0,0][1080,1920]">
    <node index="0" text="Bejelentkezés" resource-id="com.example:id/login"
          class="android.widget.Button" content-desc="" clickable="true" enabled="true"
          selected="false" bounds="[220,700][860,820]" />
    <node index="1" text="" resource-id="com.example:id/email" class="android.widget.EditText"
          content-desc="" clickable="true" enabled="true" selected="false"
          bounds="[100,400][980,480]" />
    <node index="2" text="" resource-id="" class="android.view.View" content-desc=""
          clickable="false" enabled="true" selected="false" bounds="[0,0][0,0]" />
  </node>
</hierarchy>
"""


def test_parse_ui_elements_extracts_clickable_and_editable():
    elements = parse_ui_elements(SAMPLE_XML)
    # A harmadik (dekorativ, ures) node-ot ki kell szurnie.
    assert len(elements) == 2

    button = next(e for e in elements if e["resource_id"].endswith("login"))
    assert button["text"] == "Bejelentkezés"
    assert button["clickable"] is True
    assert button["editable"] is False
    assert button["center"] == [540, 760]
    assert button["bounds"] == [220, 700, 860, 820]

    email = next(e for e in elements if e["resource_id"].endswith("email"))
    assert email["editable"] is True


def test_parse_ui_elements_handles_invalid_xml_gracefully():
    assert parse_ui_elements("not xml at all <<<") == []


def test_find_matching_elements_by_text_partial_case_insensitive():
    elements = parse_ui_elements(SAMPLE_XML)
    matches = find_matching_elements(elements, text="bejelentkez")
    assert len(matches) == 1
    assert matches[0]["resource_id"].endswith("login")


def test_find_matching_elements_by_resource_id():
    elements = parse_ui_elements(SAMPLE_XML)
    matches = find_matching_elements(elements, resource_id="email")
    assert len(matches) == 1
    assert matches[0]["editable"] is True


def test_find_matching_elements_exact_mode():
    elements = parse_ui_elements(SAMPLE_XML)
    assert find_matching_elements(elements, text="Bejelentkez", exact=True) == []
    assert len(find_matching_elements(elements, text="Bejelentkezés", exact=True)) == 1


def test_format_element_contains_key_fields():
    elements = parse_ui_elements(SAMPLE_XML)
    button = next(e for e in elements if e["resource_id"].endswith("login"))
    formatted = format_element(button)
    assert "Bejelentkezés" in formatted
    assert "login" in formatted
    assert "(540, 760)" in formatted


@pytest.mark.parametrize("package", ["com.example.app", "com.example.app.sub", "org.a.b"])
def test_validate_package_name_accepts_valid(package):
    assert validate_package_name(package) == package


@pytest.mark.parametrize("package", [
    "com.example; rm -rf /",
    "com",
    "",
    "com.example`whoami`",
    "com.example && echo hi",
])
def test_validate_package_name_rejects_invalid(package):
    with pytest.raises(ValueError):
        validate_package_name(package)


@pytest.mark.parametrize("code", ["KEYCODE_HOME", "KEYCODE_A", "KEYCODE_VOLUME_UP"])
def test_validate_keycode_accepts_valid(code):
    assert validate_keycode(code) == code


@pytest.mark.parametrize("code", ["KEYCODE_HOME; rm -rf /", "home", "KEYCODE_HOME`x`", ""])
def test_validate_keycode_rejects_invalid(code):
    with pytest.raises(ValueError):
        validate_keycode(code)


def test_sh_quote_neutralizes_shell_metacharacters():
    dangerous = "/sdcard; rm -rf /"
    quoted = sh_quote(dangerous)
    # A shlex.quote altal visszaadott string egyetlen argumentumkent ertelmezendo -
    # a pontosvesszo nem szakithatja meg parancskent.
    assert quoted.startswith("'") and quoted.endswith("'")
    assert ";" in quoted  # a karakter MEGVAN a stringben, de idezett literalkent
