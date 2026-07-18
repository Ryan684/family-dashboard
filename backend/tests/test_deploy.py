"""Tests for scripts/deploy.sh — nightly auto-deploy."""

import os
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY_SCRIPT = REPO_ROOT / "scripts" / "deploy.sh"

pytestmark = pytest.mark.skipif(
    not DEPLOY_SCRIPT.exists(),
    reason="deploy.sh not present in this environment",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bin(tmp: Path) -> Path:
    """Return a bin/ directory prepended to PATH for mock commands."""
    d = tmp / "bin"
    d.mkdir()
    return d


def _stub(bin_dir: Path, name: str, *, exit_code: int = 0, record: bool = True) -> Path:
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


def _git_stub(bin_dir: Path, *, local_sha: str, remote_sha: str, pull_code: int = 0) -> dict:
    """
    Write a git stub that implements:
      git rev-parse HEAD            → local_sha
      git rev-parse origin/main     → remote_sha
      git fetch origin main         → exit 0
      git pull origin main          → exit pull_code
    Records all invocations.
    """
    log = bin_dir.parent / "git.calls"
    script = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        echo "$@" >> {log}
        case "$*" in
          "rev-parse HEAD")        echo "{local_sha}" ;;
          "rev-parse origin/main") echo "{remote_sha}" ;;
          "fetch origin main")     exit 0 ;;
          "pull origin main")      exit {pull_code} ;;
        esac
        exit 0
    """)
    p = bin_dir / "git"
    p.write_text(script)
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return {"log": log}


def _events_stub(
    bin_dir: Path, events_log: Path, name: str, *, body: str = "exit 0"
) -> Path:
    """Write a stub that appends its invocation to a shared, ordered events log.

    Unlike `_stub`, which writes per-command call logs with no way to tell
    interleaving between commands, this lets a test assert *ordering*
    (e.g. "all pgrep checks happened before the relaunch").
    """
    script = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        echo "{name} $@" >> {events_log}
        {body}
    """)
    p = bin_dir / name
    p.write_text(script)
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return p


def _pgrep_eventually_gone_stub(
    bin_dir: Path, events_log: Path, *, still_running_calls: int
) -> Path:
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


def _make_sudo_stub(bin_dir: Path) -> None:
    """Write a sudo stub that re-executes its args with the custom PATH intact."""
    script = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        exec "$@"
    """)
    p = bin_dir / "sudo"
    p.write_text(script)
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _run_deploy(
    tmp: Path,
    bin_dir: Path,
    *,
    deployed_sha: str | None = None,
) -> subprocess.CompletedProcess:
    """
    Run deploy.sh in an isolated fake repo dir.

    deployed_sha: if provided, writes .last-deployed-sha with this value to
                  simulate a prior successful deploy; if None, no marker exists.
    """
    repo_root = tmp / "repo"
    (repo_root / "frontend").mkdir(parents=True, exist_ok=True)
    (repo_root / "backend").mkdir(parents=True, exist_ok=True)

    if deployed_sha is not None:
        (repo_root / ".last-deployed-sha").write_text(deployed_sha)

    _make_sudo_stub(bin_dir)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env["DEPLOY_REPO_DIR"] = str(repo_root)
    # Point the venv pip to our stub pip so tests don't need a real venv.
    env["DEPLOY_VENV_PIP"] = str(bin_dir / "pip")
    env["HOME"] = str(tmp)
    return subprocess.run(
        ["bash", str(DEPLOY_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Scenario: already successfully deployed — nothing happens
# ---------------------------------------------------------------------------


def test_no_action_when_sha_matches(tmp_path):
    b = _make_bin(tmp_path)
    same = "abc123"
    _git_stub(b, local_sha=same, remote_sha=same)
    npm_log = _stub(b, "npm")
    pip_log = _stub(b, "pip")
    systemctl_log = _stub(b, "systemctl")

    result = _run_deploy(tmp_path, b, deployed_sha=same)

    assert result.returncode == 0
    assert _calls(npm_log) == []
    assert _calls(pip_log) == []
    assert _calls(systemctl_log) == []


# ---------------------------------------------------------------------------
# Scenario: new commits available — full deploy
# ---------------------------------------------------------------------------


def test_full_deploy_when_sha_differs(tmp_path):
    b = _make_bin(tmp_path)
    _git_stub(b, local_sha="aaa", remote_sha="bbb")
    npm_log = _stub(b, "npm")
    pip_log = _stub(b, "pip")
    systemctl_log = _stub(b, "systemctl")
    _stub(b, "pkill")
    _stub(b, "pgrep", exit_code=1)
    _stub(b, "setsid")
    _stub(b, "sleep")

    result = _run_deploy(tmp_path, b)

    assert result.returncode == 0
    assert any("run" in c and "build" in c for c in _calls(npm_log)), _calls(npm_log)
    assert any("install" in c for c in _calls(pip_log)), _calls(pip_log)
    assert any("restart" in c and "family-dashboard" in c for c in _calls(systemctl_log)), _calls(systemctl_log)


# ---------------------------------------------------------------------------
# Scenario: git pull fails — abort before build
# ---------------------------------------------------------------------------


def test_abort_on_git_pull_failure(tmp_path):
    b = _make_bin(tmp_path)
    _git_stub(b, local_sha="aaa", remote_sha="bbb", pull_code=1)
    npm_log = _stub(b, "npm")
    systemctl_log = _stub(b, "systemctl")
    _stub(b, "pip")

    result = _run_deploy(tmp_path, b)

    assert result.returncode != 0
    assert _calls(npm_log) == []
    assert _calls(systemctl_log) == []


# ---------------------------------------------------------------------------
# Scenario: npm build fails — abort before restart
# ---------------------------------------------------------------------------


def test_abort_on_npm_build_failure(tmp_path):
    b = _make_bin(tmp_path)
    _git_stub(b, local_sha="aaa", remote_sha="bbb")
    npm_log = _stub(b, "npm", exit_code=1)
    systemctl_log = _stub(b, "systemctl")
    _stub(b, "pip")

    result = _run_deploy(tmp_path, b)

    assert result.returncode != 0
    assert any("run" in c and "build" in c for c in _calls(npm_log)), _calls(npm_log)
    assert _calls(systemctl_log) == []


# ---------------------------------------------------------------------------
# Scenario: Chromium restarted after successful deploy
# ---------------------------------------------------------------------------


def test_chromium_restarted_after_deploy(tmp_path):
    b = _make_bin(tmp_path)
    _git_stub(b, local_sha="aaa", remote_sha="bbb")
    _stub(b, "npm")
    _stub(b, "pip")
    _stub(b, "systemctl")
    _stub(b, "sleep")
    pkill_log = _stub(b, "pkill")
    _stub(b, "pgrep", exit_code=1)
    setsid_log = _stub(b, "setsid")

    result = _run_deploy(tmp_path, b)

    assert result.returncode == 0
    assert any("chromium" in c for c in _calls(pkill_log)), _calls(pkill_log)
    assert any("chromium" in c for c in _calls(setsid_log)), _calls(setsid_log)


# ---------------------------------------------------------------------------
# Scenario: relaunch waits for the old Chromium process to fully exit
#
# A fixed `sleep 5` races a slow shutdown: if the old process is still
# alive when the new one starts, Chromium's single-instance mechanism
# forwards the URL to the dying process as an ordinary new window,
# silently dropping --kiosk — the exact bug reported on the Pi.
# ---------------------------------------------------------------------------


def test_relaunch_waits_for_old_chromium_to_exit(tmp_path):
    b = _make_bin(tmp_path)
    _git_stub(b, local_sha="aaa", remote_sha="bbb")
    _stub(b, "npm")
    _stub(b, "pip")
    _stub(b, "systemctl")
    _stub(b, "pkill")
    events_log = tmp_path / "events.log"
    _events_stub(b, events_log, "sleep")
    _pgrep_eventually_gone_stub(b, events_log, still_running_calls=3)
    _events_stub(b, events_log, "setsid")

    result = _run_deploy(tmp_path, b)

    assert result.returncode == 0
    events = events_log.read_text().splitlines() if events_log.exists() else []
    pgrep_calls = [e for e in events if e.startswith("pgrep")]
    setsid_calls = [e for e in events if e.startswith("setsid")]
    assert len(pgrep_calls) >= 4, events  # 3 "still running" + at least 1 "gone" check
    assert setsid_calls, (
        "chromium should still be relaunched once the old process is gone"
    )
    # the relaunch must come after the process was confirmed gone, not before
    assert events.index(setsid_calls[0]) > events.index(pgrep_calls[-1]), events


# ---------------------------------------------------------------------------
# Scenario: relaunch force-kills Chromium if it never exits cleanly
# ---------------------------------------------------------------------------


def test_relaunch_force_kills_chromium_after_bounded_wait(tmp_path):
    b = _make_bin(tmp_path)
    _git_stub(b, local_sha="aaa", remote_sha="bbb")
    _stub(b, "npm")
    _stub(b, "pip")
    _stub(b, "systemctl")
    _stub(b, "sleep")
    pkill_log = _stub(b, "pkill")
    _stub(b, "pgrep", exit_code=0)  # always reports chromium as still running
    setsid_log = _stub(b, "setsid")

    result = _run_deploy(tmp_path, b)

    assert result.returncode == 0
    assert any("-9" in c for c in _calls(pkill_log)), _calls(pkill_log)
    assert any("chromium" in c for c in _calls(setsid_log)), (
        "chromium should still be relaunched even after a stuck old process"
    )


# ---------------------------------------------------------------------------
# Scenario: Chromium not restarted when already successfully deployed
# ---------------------------------------------------------------------------


def test_chromium_not_restarted_when_up_to_date(tmp_path):
    b = _make_bin(tmp_path)
    same = "abc123"
    _git_stub(b, local_sha=same, remote_sha=same)
    _stub(b, "npm")
    _stub(b, "pip")
    _stub(b, "systemctl")
    _stub(b, "sleep")
    pkill_log = _stub(b, "pkill")
    _stub(b, "setsid")

    result = _run_deploy(tmp_path, b, deployed_sha=same)

    assert result.returncode == 0
    assert _calls(pkill_log) == []


# ---------------------------------------------------------------------------
# Scenario: pip install uses the backend virtual environment
# ---------------------------------------------------------------------------


def test_pip_install_uses_venv_not_system_pip3(tmp_path):
    b = _make_bin(tmp_path)
    _git_stub(b, local_sha="aaa", remote_sha="bbb")
    _stub(b, "npm")
    pip_log = _stub(b, "pip")
    pip3_log = _stub(b, "pip3")
    _stub(b, "systemctl")
    _stub(b, "pkill")
    _stub(b, "pgrep", exit_code=1)
    _stub(b, "setsid")
    _stub(b, "sleep")

    result = _run_deploy(tmp_path, b)

    assert result.returncode == 0
    assert any("install" in c for c in _calls(pip_log)), _calls(pip_log)
    assert _calls(pip3_log) == [], f"pip3 should not be called; got: {_calls(pip3_log)}"


# ---------------------------------------------------------------------------
# Scenario: marker file written after successful deploy
# ---------------------------------------------------------------------------


def test_successful_deploy_writes_marker(tmp_path):
    b = _make_bin(tmp_path)
    _git_stub(b, local_sha="aaa", remote_sha="bbb")
    _stub(b, "npm")
    _stub(b, "pip")
    _stub(b, "systemctl")
    _stub(b, "pkill")
    _stub(b, "pgrep", exit_code=1)
    _stub(b, "setsid")
    _stub(b, "sleep")

    result = _run_deploy(tmp_path, b)

    assert result.returncode == 0
    marker = tmp_path / "repo" / ".last-deployed-sha"
    assert marker.exists(), "marker file should be written after successful deploy"
    assert marker.read_text().strip() == "bbb"


# ---------------------------------------------------------------------------
# Scenario: marker file NOT written when deploy fails
# ---------------------------------------------------------------------------


def test_failed_deploy_does_not_write_marker(tmp_path):
    b = _make_bin(tmp_path)
    _git_stub(b, local_sha="aaa", remote_sha="bbb")
    _stub(b, "npm", exit_code=1)
    _stub(b, "pip")
    _stub(b, "systemctl")

    result = _run_deploy(tmp_path, b)

    assert result.returncode != 0
    marker = tmp_path / "repo" / ".last-deployed-sha"
    assert not marker.exists(), "marker file must not be written when deploy fails"


# ---------------------------------------------------------------------------
# Scenario: previously failed partial deploy is retried
# (HEAD already matches origin/main due to prior git pull, but no marker file)
# ---------------------------------------------------------------------------


def test_failed_deploy_is_retried_on_next_run(tmp_path):
    b = _make_bin(tmp_path)
    same_sha = "abc123"
    # Simulate: git pull already ran in a previous failed attempt — HEAD == origin/main
    _git_stub(b, local_sha=same_sha, remote_sha=same_sha)
    npm_log = _stub(b, "npm")
    pip_log = _stub(b, "pip")
    systemctl_log = _stub(b, "systemctl")
    _stub(b, "pkill")
    _stub(b, "pgrep", exit_code=1)
    _stub(b, "setsid")
    _stub(b, "sleep")
    # No deployed_sha → no marker file → must retry despite HEAD == origin/main

    result = _run_deploy(tmp_path, b)

    assert result.returncode == 0
    assert any("run" in c and "build" in c for c in _calls(npm_log)), _calls(npm_log)
    assert any("install" in c for c in _calls(pip_log)), _calls(pip_log)
    assert any("restart" in c and "family-dashboard" in c for c in _calls(systemctl_log)), _calls(systemctl_log)
