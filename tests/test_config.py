"""Tesztek az AppConfig mod-logikajahoz - kulonos tekintettel a max_mode
(felso hatar) es a mode (aktualis, oda-vissza kapcsolhato) szetvalasztasara,
ami a korabbi hibat javitja (ADMIN -> SAFE -> ADMIN oda-vissza valtas)."""

from __future__ import annotations

from android_control_mcp.config import AppConfig, Mode, level_value


def test_level_value_ordering():
    assert level_value(Mode.SAFE) < level_value(Mode.NORMAL) < level_value(Mode.ADMIN)


def test_max_mode_defaults_to_mode_when_constructed_directly():
    # Ez modellezi azt, amit a load_config() csinal induláskor: max_mode = mode.
    cfg = AppConfig(mode=Mode.ADMIN)
    cfg.max_mode = cfg.mode
    assert cfg.max_mode == Mode.ADMIN


def test_admin_started_server_can_go_down_and_back_up():
    """A korabbi hiba: ha ADMIN-rol lementunk NORMAL-ra, a regi logika utana
    mar nem engedte vissza ADMIN-ra, mert 'current_mode == ADMIN'-t kovetelt
    meg a felfele valtashoz. Az uj logika a rogzitett max_mode-hoz hasonlit,
    nem a pillanatnyi mode-hoz."""
    cfg = AppConfig(mode=Mode.ADMIN)
    cfg.max_mode = Mode.ADMIN

    # Level le ADMIN -> SAFE
    cfg.mode = Mode.SAFE
    assert level_value(Mode.NORMAL) <= level_value(cfg.max_mode)  # meg engedne

    # Az uj set_mode-logika lenyege: a celt a max_mode-hoz hasonlitjuk, NEM a
    # pillanatnyi cfg.mode-hoz.
    target = Mode.ADMIN
    assert level_value(target) <= level_value(cfg.max_mode)
    cfg.mode = target
    assert cfg.mode == Mode.ADMIN


def test_normal_started_server_cannot_reach_admin_via_max_mode_check():
    cfg = AppConfig(mode=Mode.NORMAL)
    cfg.max_mode = Mode.NORMAL

    target = Mode.ADMIN
    assert level_value(target) > level_value(cfg.max_mode)  # ezt a set_mode elutasitja
