"""Celzott regressziós teszt a review 4. pontjara: a scrcpy-session-inditasnak
NEM szabad sikeresnek tunnie, ha a folyamat rovid idon belul (driver/USB/AOA
hiba miatt) kilep. Valodi, rovid eletu Python-alfolyamatokkal teszteljuk -
nincs szukseg tenyleges scrcpy binarisra vagy Android eszkozre.

Minden teszt EGYETLEN 'asyncio.run()' hivason belul fut le (a start es a
stop is ugyanabban a loop-ban) - windowsos ProactorEventLoop alatt egy
subprocess-transport nem adhato at kulon 'asyncio.run()' hivasok (=kulon
event loop-ok) kozott, ami a valodi szerverben (egyetlen, vegig futo loop)
sose fordulna elo, de egy naiv tesztben felreveto hibat okozna.
"""

from __future__ import annotations

import asyncio
import sys
from unittest.mock import AsyncMock, patch

import pytest

from android_control_mcp.rescue import session as session_module
from android_control_mcp.rescue.scrcpy_binary import ScrcpyInfo


@pytest.fixture(autouse=True)
def _fast_health_check(monkeypatch):
    """A valodi 1.0s-os health-check-kesleltetes feleslegesen lassitana a
    teszteket - itt egy nagyon rovidre allitjuk, a viselkedes ugyanaz marad."""
    monkeypatch.setattr(session_module, "_STARTUP_HEALTH_CHECK_DELAY", 0.15)
    yield
    session_module._active_sessions.clear()


def _fake_scrcpy_info():
    return ScrcpyInfo(executable=sys.executable, version="fake-test-build", available=True,
                       detail="ok")


def _with_profile(script_args):
    """Context manager-szeru helper: ideiglenesen lecsereli a 'balanced'
    profil kapcsoloit egy 'python -c <script>' hivasra, majd visszaallitja."""
    original = session_module.PROFILES["balanced"]
    session_module.PROFILES["balanced"] = script_args
    return original


def test_start_mirror_session_raises_on_immediate_exit_with_stderr():
    """A legfontosabb eset: a 'scrcpy' (itt: egy Python-szkript, ami rogton
    kilep hibaval) NEM regisztralodhat sikeres sessionkent."""
    script = "import sys; sys.stderr.write('AOA device not found\\n'); sys.exit(1)"
    original = _with_profile(["-c", script])

    async def run():
        with patch("android_control_mcp.rescue.session.detect_scrcpy",
                   new=AsyncMock(return_value=_fake_scrcpy_info())):
            with pytest.raises(RuntimeError) as excinfo:
                await session_module.start_mirror_session(None, profile="balanced")
            return excinfo

    try:
        excinfo = asyncio.run(run())
    finally:
        session_module.PROFILES["balanced"] = original

    assert "AOA device not found" in str(excinfo.value)
    assert "kilepett" in str(excinfo.value)
    assert len(session_module.list_sessions()) == 0


def test_start_mirror_session_succeeds_when_process_stays_alive():
    """Ha a folyamat tulel a health-check-ablakon, sikeres sessionkent kell
    visszaadni, es a registryben is szerepelnie kell - majd 'stop_session'-nel
    tenylegesen le is all."""
    script = "import time; time.sleep(5)"
    original = _with_profile(["-c", script])

    async def run():
        with patch("android_control_mcp.rescue.session.detect_scrcpy",
                   new=AsyncMock(return_value=_fake_scrcpy_info())):
            sess = await session_module.start_mirror_session(None, profile="balanced")
            assert sess.is_running()
            assert sess.pid in [s.pid for s in session_module.list_sessions()]

            await session_module.stop_session(sess.pid)
            assert not sess.is_running()
            assert sess.pid not in [s.pid for s in session_module.list_sessions()]

    try:
        asyncio.run(run())
    finally:
        session_module.PROFILES["balanced"] = original


def test_read_only_mirror_appends_official_scrcpy_no_input_flags():
    """read_only=True eseten a valodi, hivatalos scrcpy sajat kapcsoloit kell
    hasznalni (--no-control/--no-audio/--no-clipboard-autosync) - nem sajat
    kitalalt flaget. Itt egy fake 'scrcpy'-t (python -c) inditunk, ami csak
    kiirja a sajat argv-jet, hogy ellenorizhessuk, ezek a kapcsolok tenyleg
    megjelennek a folyamat parancssoraban."""
    script = (
        "import sys, time; print(' '.join(sys.argv[1:]), flush=True); time.sleep(5)"
    )
    original = _with_profile(["-c", script])

    async def run():
        with patch("android_control_mcp.rescue.session.detect_scrcpy",
                   new=AsyncMock(return_value=_fake_scrcpy_info())):
            sess = await session_module.start_mirror_session(
                None, profile="balanced", read_only=True, print_fps=True,
            )
            try:
                assert "--no-control" in sess.args
                assert "--no-audio" in sess.args
                assert "--no-clipboard-autosync" in sess.args
                assert "--print-fps" in sess.args
                # Adjunk a stdout-pumpanak egy kis idot, hogy elolvassa a sort.
                await asyncio.sleep(0.3)
                assert any("--no-control" in line for line in sess.stdout_tail), (
                    f"A stdout-pumpa nem kapta el a fake-scrcpy sajat argv-jenek "
                    f"kiirasat: {list(sess.stdout_tail)!r}"
                )
            finally:
                await session_module.stop_session(sess.pid)

    try:
        asyncio.run(run())
    finally:
        session_module.PROFILES["balanced"] = original


def test_default_mirror_does_not_add_read_only_flags():
    """Alapertelmezetten (read_only=False) a normal vezerelt tukrozes NEM kap
    --no-control-t - ne korlatozzuk veletlenul a normal hasznalatot."""
    original = _with_profile(["-c", "import time; time.sleep(5)"])

    async def run():
        with patch("android_control_mcp.rescue.session.detect_scrcpy",
                   new=AsyncMock(return_value=_fake_scrcpy_info())):
            sess = await session_module.start_mirror_session(None, profile="balanced")
            try:
                assert "--no-control" not in sess.args
                assert "--print-fps" not in sess.args
            finally:
                await session_module.stop_session(sess.pid)

    try:
        asyncio.run(run())
    finally:
        session_module.PROFILES["balanced"] = original


def test_last_fps_line_extracts_most_recent_fps_entry():
    """A stdout-pufferbol a legutolso 'fps'-t tartalmazo sort kell
    visszaadnia (--print-fps valodi kimenetenek formatuma, pl. '61 fps')."""
    script = (
        "import sys, time\n"
        "print('INFO: Renderer: direct3d11', flush=True)\n"
        "print('INFO: 48 fps (+17 frames skipped)', flush=True)\n"
        "print('INFO: 61 fps', flush=True)\n"
        "time.sleep(5)\n"
    )
    original = _with_profile(["-c", script])

    async def run():
        with patch("android_control_mcp.rescue.session.detect_scrcpy",
                   new=AsyncMock(return_value=_fake_scrcpy_info())):
            sess = await session_module.start_mirror_session(
                None, profile="balanced", print_fps=True,
            )
            try:
                await asyncio.sleep(0.3)
                assert sess.last_fps_line() == "INFO: 61 fps"
            finally:
                await session_module.stop_session(sess.pid)

    try:
        asyncio.run(run())
    finally:
        session_module.PROFILES["balanced"] = original


def test_prune_dead_sessions_cleans_up_on_next_start():
    """Egy korabban elhalt session automatikusan eltunik a
    nyilvantartasbol a kovetkezo session-inditaskor."""

    async def run():
        with patch("android_control_mcp.rescue.session.detect_scrcpy",
                   new=AsyncMock(return_value=_fake_scrcpy_info())):
            original = _with_profile(["-c", "import time; time.sleep(5)"])
            try:
                sess1 = await session_module.start_mirror_session(None, profile="balanced")
            finally:
                session_module.PROFILES["balanced"] = original

            sess1.process.terminate()
            await sess1.process.wait()  # ugyanabban a loop-ban, mint ami inditotta
            assert not sess1.is_running()

            original = _with_profile(["-c", "import sys; sys.exit(1)"])
            try:
                with pytest.raises(RuntimeError):
                    await session_module.start_mirror_session(None, profile="balanced")
            finally:
                session_module.PROFILES["balanced"] = original

            assert sess1.pid not in [s.pid for s in session_module.list_sessions()]

    asyncio.run(run())
