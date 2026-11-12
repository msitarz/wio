# SPDX-License-Identifier: Apache-2.0
"""What the tests of the hooks that run a `wio` check share.

A hook is run as the harness runs it, with the edited file's JSON on standard
input, and a fake `uv` stands for the check: it prints what it is told and exits
as it is told, and refuses any other command line. It leaves a marker when it
is run with the right one, so a hook that is silent can be told from one that
never called the check.
"""

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FAKE_UV = """#!/bin/sh
# A stand-in for `uv run wio <check>`: prints a message, exits as told.
[ "$*" = "run wio $FAKE_CHECK" ] || exit 70
: > "$FAKE_CHECK_CALLED"
printf '%s\\n' "$FAKE_CHECK_OUTPUT"
exit "$FAKE_CHECK_EXIT"
"""
CALLED = "check-called"
"""The name of the marker that the fake `uv` leaves in the directory it is in."""
NEEDS_JQ = pytest.mark.skipif(shutil.which("jq") is None, reason="needs jq")
"""Skips a test that runs the hook's command, which reads its input with `jq`."""


def check_was_called(tmp_path: Path) -> bool:
    """Tell whether the fake `uv` was run with the check's command line.

    Args:
        tmp_path: The directory that was given to `run_hook`.

    Returns:
        Whether the hook called the check, whatever it did with the result.
    """
    return (tmp_path / CALLED).exists()


def find_hook(check: str) -> dict[str, object]:
    """Find the `PostToolUse` hook of `.claude/settings.json` that runs a check.

    Args:
        check: The check's command line, such as `uv run wio config check`.

    Returns:
        The one hook whose `command` runs it, after asserting that it is the only
        one and that it runs after `Edit`, `Write` and `MultiEdit`.
    """
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
    found = [
        (entry["matcher"], hook)
        for entry in settings["hooks"]["PostToolUse"]
        for hook in entry["hooks"]
        if check in hook["command"]
    ]
    assert len(found) == 1
    matcher, hook = found[0]
    assert set(matcher.split("|")) == {"Edit", "Write", "MultiEdit"}
    return hook


def run_hook(
    hook: dict[str, object],
    tmp_path: Path,
    file_path: str,
    *,
    check: str,
    exit_code: int,
    output: str,
) -> tuple[int, str, str]:
    """Run the command of a hook with a fake `uv` that stands for the check.

    Args:
        hook: The hook, as `find_hook` returns it.
        tmp_path: A directory for the fake `uv`.
        file_path: The path the hook's JSON names as the edited file.
        check: What the fake `uv` accepts after `uv run wio`, such as `config check`.
        exit_code: The exit code of the fake check.
        output: The line that the fake check prints on standard output.

    Returns:
        The exit code, standard output and standard error of the hook.
    """
    uv = tmp_path / "uv"
    uv.write_text(FAKE_UV)
    uv.chmod(uv.stat().st_mode | stat.S_IXUSR)
    env = {
        "PATH": f"{tmp_path}:/usr/bin:/bin",
        "FAKE_CHECK": check,
        "FAKE_CHECK_EXIT": str(exit_code),
        "FAKE_CHECK_OUTPUT": output,
        "FAKE_CHECK_CALLED": str(tmp_path / CALLED),
    }
    done = subprocess.run(
        ["/bin/sh", "-c", str(hook["command"])],
        input=json.dumps({"tool_input": {"file_path": file_path}}),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return done.returncode, done.stdout, done.stderr


def run_prek(tmp_path: Path, files: dict[str, str], hook: str) -> tuple[int, str]:
    """Run one hook of `prek.toml` on the staged files of a new repository.

    The repository is a new git repository under `tmp_path/repo` that holds
    `files`, all staged, and a `prek.toml` that is a copy of this repository's with
    only its `repo = "local"` section: selecting one hook does not keep `prek` from
    preparing the other repositories, and the remote ones need the network. `prek`
    gets a home of its own under `tmp_path`, outside the repository, so it touches
    no cache of the user's and `git add` finds no embedded repository. `prek` is
    the one that is installed beside this interpreter, `Path(sys.executable).parent
    / "prek"`, because it is not on the `PATH`, and a shim in front of the `PATH`
    stands for `uv`: for `uv run wio` it runs the `wio` installed beside this
    interpreter, so the hook runs the real check without a project to resolve.

    Args:
        tmp_path: A directory for the repository, the shim and the home of `prek`.
        files: The files to stage, by path relative to the repository's root,
            which include the config and the templates that the check needs.
        hook: The id of the hook, such as `wio-contracts`.

    Returns:
        The exit code of `prek`, which is not 0 when the hook fails, and its output,
        standard output and standard error together. The caller skips when `git`
        or `prek` is missing.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    prek_toml = (ROOT / "prek.toml").read_text()
    local = prek_toml[prek_toml.index('[[repos]]\nrepo = "local"') :]
    (repo / "prek.toml").write_text(local)
    for name, text in files.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    bin_dir = Path(sys.executable).parent
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    shim = shim_dir / "uv"
    shim.write_text(
        '#!/bin/sh\n[ "$1 $2" = "run wio" ] || exit 70\nshift 2\n'
        f'exec "{bin_dir / "wio"}" "$@"\n'
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
    env = {
        **os.environ,
        "PATH": f"{shim_dir}:{os.environ['PATH']}",
        "HOME": str(tmp_path / "home"),
        "PREK_HOME": str(tmp_path / "prek-home"),
        "NO_COLOR": "1",
    }
    (tmp_path / "home").mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, env=env, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    done = subprocess.run(
        [str(bin_dir / "prek"), "run", hook],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return done.returncode, done.stdout + done.stderr
