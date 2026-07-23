"""Tests for scripts/restart-kiosk.sh — Chromium kiosk restart.

Chained onto the crontab line that powers the display on at 06:30
(`wlopm --on HDMI-A-1 && .../restart-kiosk.sh`), so Chromium only ever
starts once the Wayland output is confirmed live. Previously this logic
lived inside deploy.sh and ran at 02:00 — squarely inside the 22:00-06:30
display-off window — which left Chromium permanently windowed every single
time, not intermittently, because a fullscreen request has no live output
to negotiate against while the display is off. See hardware.md, "Known
issue: Chromium doesn't go fullscreen when launched while the display is
off".

Unlike deploy.sh, this script carries no SHA/marker-file gating — it
restarts Chromium unconditionally every time it's invoked.
"""

import os
import re
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RESTART_SCRIPT = REPO_ROOT / "scripts" / "restart-kiosk.sh"

pytestmark = pytest.mark.skipif(
    not RESTART_SCRIPT.exists(),
    reason="restart-kiosk.sh not present in this environment",
)

TIMESTAMP_RE = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"

# ---------------------------------------------------------------------------
# Helpers (mirrors backend/tests/test_deploy.py's stub patterns)
# ---------------------------------------------------------------------------


def _make_bin(tmp: Path) -> Path:
    d = tmp / "bin"
    d.mkdir()
    return d


def _stub(bin_dir: Path, name: str, *, exit_code: int = 0) -> Path:
    """Write an executable stub that records invocations and returns exit_code."""
    log = bin_dir.parent / f"{name}.calls"
    script = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        echo "$@" >> {log}
        exit {exit_code}
    """)
    p = bin_dir / name
    p.write_text(script)
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return log


def _calls(log: Path) -> list[str]:
    if not log.exists():
        return []
    return [line.strip() for line in log.read_text().splitlines() if line.strip()]


def _events_stub(bin_dir: Path, events_log: Path, name: str, *, body: str = "exit 0") -> Path:
    """Write a stub that appends its invocation to a shared, ordered events log."""
    script = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        echo "{name} $@" >> {events_log}
        {body}
    """)
    p = bin_dir / name
    p.write_text(script)
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return p


def _pgrep_eventually_gone_stub(bin_dir: Path, events_log: Path, *, still_running_calls: int) -> Path:
    """pgrep stub: reports the process as running for the first N calls, then gone."""
    counter_file = bin_dir.parent / "pgrep.count"
    body = textwrap.dedent(f"""\
        count=$(( $(cat "{counter_file}" 2>/dev/null || echo 0) + 1 ))
        echo "$count" > "{counter_file}"
        if [ "$count" -le {still_running_calls} ]; then
            exit 0
        else
            exit 1
        fi
    """)
    return _events_stub(bin_dir, events_log, "pgrep", body=body)


def _run_restart_kiosk(tmp: Path, bin_dir: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env["HOME"] = str(tmp)
    env["KIOSK_CHROME_PROFILE_DIR"] = str(tmp / ".cache" / "chromium-kiosk")
    return subprocess.run(
        ["bash", str(RESTART_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Scenario: Chromium is restarted every time the script runs
# ---------------------------------------------------------------------------


def test_chromium_restarted_every_run(tmp_path):
    b = _make_bin(tmp_path)
    pkill_log = _stub(b, "pkill")
    _stub(b, "pgrep", exit_code=1)
    setsid_log = _stub(b, "setsid")
    _stub(b, "sleep")

    result = _run_restart_kiosk(tmp_path, b)

    assert result.returncode == 0
    assert any("chromium" in c for c in _calls(pkill_log)), _calls(pkill_log)
    assert any("chromium" in c for c in _calls(setsid_log)), _calls(setsid_log)


# ---------------------------------------------------------------------------
# Scenario: relaunch waits for the old Chromium process to fully exit
# ---------------------------------------------------------------------------


def test_relaunch_waits_for_old_chromium_to_exit(tmp_path):
    b = _make_bin(tmp_path)
    _stub(b, "pkill")
    events_log = tmp_path / "events.log"
    _events_stub(b, events_log, "sleep")
    _pgrep_eventually_gone_stub(b, events_log, still_running_calls=3)
    _events_stub(b, events_log, "setsid")

    result = _run_restart_kiosk(tmp_path, b)

    assert result.returncode == 0
    events = events_log.read_text().splitlines() if events_log.exists() else []
    pgrep_calls = [e for e in events if e.startswith("pgrep")]
    setsid_calls = [e for e in events if e.startswith("setsid")]
    assert len(pgrep_calls) >= 4, events
    assert setsid_calls, "chromium should still be relaunched once the old process is gone"
    assert events.index(setsid_calls[0]) > events.index(pgrep_calls[-1]), events


# ---------------------------------------------------------------------------
# Scenario: relaunch force-kills Chromium if it never exits cleanly
# ---------------------------------------------------------------------------


def test_relaunch_force_kills_chromium_after_bounded_wait(tmp_path):
    b = _make_bin(tmp_path)
    _stub(b, "sleep")
    pkill_log = _stub(b, "pkill")
    _stub(b, "pgrep", exit_code=0)  # always reports chromium as still running
    setsid_log = _stub(b, "setsid")

    result = _run_restart_kiosk(tmp_path, b)

    assert result.returncode == 0
    assert any("-9" in c for c in _calls(pkill_log)), _calls(pkill_log)
    assert any("chromium" in c for c in _calls(setsid_log)), (
        "chromium should still be relaunched even after a stuck old process"
    )


# ---------------------------------------------------------------------------
# Scenario: relaunch wipes the Chromium profile before starting
# ---------------------------------------------------------------------------


def test_relaunch_wipes_stale_chromium_profile(tmp_path):
    b = _make_bin(tmp_path)
    _stub(b, "sleep")
    _stub(b, "pkill")
    _stub(b, "pgrep", exit_code=1)
    setsid_log = _stub(b, "setsid")

    profile_dir = tmp_path / ".cache" / "chromium-kiosk"
    profile_dir.mkdir(parents=True)
    stale_marker = profile_dir / "Default" / "Preferences"
    stale_marker.parent.mkdir(parents=True)
    stale_marker.write_text('{"session": {"restore_on_startup": 1}}')

    result = _run_restart_kiosk(tmp_path, b)

    assert result.returncode == 0
    assert not stale_marker.exists(), "stale profile must be wiped before relaunch"
    setsid_calls = _calls(setsid_log)
    assert any(
        "--user-data-dir" in c and str(profile_dir) in c for c in setsid_calls
    ), setsid_calls


# ---------------------------------------------------------------------------
# Scenario: relaunch logs whether the old Chromium process exited cleanly
# ---------------------------------------------------------------------------


def test_relaunch_logs_clean_exit(tmp_path):
    b = _make_bin(tmp_path)
    _stub(b, "pkill")
    events_log = tmp_path / "events.log"
    _events_stub(b, events_log, "sleep")
    _pgrep_eventually_gone_stub(b, events_log, still_running_calls=3)
    _events_stub(b, events_log, "setsid")

    result = _run_restart_kiosk(tmp_path, b)

    assert result.returncode == 0
    assert re.search(rf"{TIMESTAMP_RE}.*exited cleanly", result.stdout), result.stdout
    assert "forced kill" not in result.stdout.lower()


def test_relaunch_logs_forced_kill(tmp_path):
    b = _make_bin(tmp_path)
    _stub(b, "sleep")
    _stub(b, "pkill")
    _stub(b, "pgrep", exit_code=0)  # always reports chromium as still running
    _stub(b, "setsid")

    result = _run_restart_kiosk(tmp_path, b)

    assert result.returncode == 0
    assert re.search(rf"{TIMESTAMP_RE}.*forced kill", result.stdout, re.IGNORECASE), result.stdout
    assert "exited cleanly" not in result.stdout.lower()
