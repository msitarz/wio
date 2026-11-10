# SPDX-License-Identifier: Apache-2.0
"""Tests of the hooks that run `wio config check` and the recipe that shows them."""

import json
import re
import tomllib
from typing import TYPE_CHECKING

import pytest

from tests.tooling.hooks import NEEDS_JQ, ROOT, find_hook, run_hook

if TYPE_CHECKING:
    from pathlib import Path

CONFIG = ".agents/wio/config.toml"
CHECK = "uv run wio config check"
DIAGNOSTIC = "error: works.nonsense: unknown key"


def _hook() -> dict[str, object]:
    """Find the `PostToolUse` hook of `.claude/settings.json` that checks the config.

    Returns:
        The hook: its `command` runs `uv run wio config check`.
    """
    return find_hook(CHECK)


def test_prek_runs_the_check_when_only_the_config_changes() -> None:
    """AC-2: the hook matches the config and passes it no file names."""
    # Given `prek.toml`
    prek = tomllib.loads((ROOT / "prek.toml").read_text())

    # When its hook for the config is read
    hooks = [
        hook
        for repo in prek["repos"]
        for hook in repo["hooks"]
        if hook.get("entry") == "uv run wio config check"
    ]

    # Then it runs `wio config check`, matches only the config, no filenames
    assert len(hooks) == 1
    hook = hooks[0]
    assert re.search(hook["files"], CONFIG)
    assert not re.search(hook["files"], "docs/workflow.md")
    assert not re.search(hook["files"], f"tests/fixtures/config/rich/{CONFIG}")
    assert hook["pass_filenames"] is False


def test_claude_settings_run_the_check_beside_the_formatter() -> None:
    """AC-3: one `PostToolUse` hook runs `uv run wio config check`."""
    # Given `.claude/settings.json`
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())

    # When its `PostToolUse` hooks are read
    hook = _hook()
    commands = [
        hook["command"]
        for entry in settings["hooks"]["PostToolUse"]
        for hook in entry["hooks"]
    ]

    # Then one runs after `Edit`, `Write` and `MultiEdit` and its command runs
    # `uv run wio config check`, and the formatter stays
    assert any("ruff format" in command for command in commands)
    assert "uv run wio config check" in str(hook["command"])


def _run_hook(tmp_path: Path, file_path: str, check_exit: int) -> tuple[int, str, str]:
    """Run the command of the hook with a fake `uv` that stands for the check.

    Args:
        tmp_path: A directory for the fake `uv`.
        file_path: The path the hook's JSON names as the edited file.
        check_exit: The exit code of the fake check.

    Returns:
        The exit code, standard output and standard error of the hook.
    """
    return run_hook(
        _hook(),
        tmp_path,
        file_path,
        check="config check",
        exit_code=check_exit,
        output=DIAGNOSTIC,
    )


@NEEDS_JQ
@pytest.mark.slow
def test_the_hook_returns_the_errors_of_an_edit_of_the_config(tmp_path: Path) -> None:
    """AC-3: the command of the hook exits 2 with the diagnostics on stderr."""
    # Given the hook's JSON for an edit of the config, and a check that fails
    path = f"/work/{CONFIG}"

    # When the command of the hook runs with that JSON on standard input
    code, out, err = _run_hook(tmp_path, path, check_exit=1)

    # Then it prints the diagnostics to standard error and exits 2
    assert code == 2
    assert out == ""
    assert err == f"{DIAGNOSTIC}\n"


@NEEDS_JQ
@pytest.mark.slow
@pytest.mark.parametrize(
    ("file_path", "check_exit"),
    [("/work/.agents/wio/other.toml", 1), (f"/work/{CONFIG}", 0)],
    ids=["another TOML file", "config without errors"],
)
def test_the_hook_is_silent_for_other_edits_and_a_clean_config(
    tmp_path: Path, file_path: str, check_exit: int
) -> None:
    """AC-3: the command of the hook exits 0 and prints nothing."""
    # Given the hook's JSON for another TOML file, and for a clean config
    # When the command of the hook runs with it on standard input
    code, out, err = _run_hook(tmp_path, file_path, check_exit)

    # Then it exits 0 and prints nothing
    assert (code, out, err) == (0, "", "")


def test_the_workflow_shows_the_recipe() -> None:
    """AC-4: the doc has the entry, "each project" and the prek hook."""
    # Given `docs/workflow.md`
    text = " ".join((ROOT / "docs" / "workflow.md").read_text().split())

    # When it is read
    # Then it shows the `PostToolUse` entry, says each project decides how, writes
    # `wio config check` for a global install, and says when the prek hook runs
    assert '"PostToolUse"' in text
    assert "uv run wio config check" in text
    assert "each project decides" in text
    assert "writes `wio config check`" in text
    assert "`wio-config` hook of `prek.toml` runs" in text
