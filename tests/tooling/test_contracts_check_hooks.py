# SPDX-License-Identifier: Apache-2.0
"""Tests of the hooks that run `wio contracts check`."""

import re
import shutil
import tomllib
from functools import partial
from typing import TYPE_CHECKING

import pytest

from tests.tooling.hooks import (
    NEEDS_JQ,
    ROOT,
    check_was_called,
    find_hook,
    run_hook,
    run_prek,
)

if TYPE_CHECKING:
    from pathlib import Path

CHECK = "uv run wio contracts check"
WORKS = "/work/.agents/wio/works"
DIAGNOSTIC = (
    "error: .agents/wio/works/a/README.md: The dependency `zzzzzz` is not a Work"
)
CONFIG = ROOT / "tests/fixtures/contracts/check-clean/.agents/wio/config.toml"
NEEDS_GIT = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
BROKEN = '<!-- wio\nid = "hok001"\ndepends_on = ["zzzzzz"]\n-->\n\n# Title\n'


_RUN = partial(run_hook, check="contracts check")
"""Runs the command of a hook with a fake `uv` that stands for the contracts check."""


@NEEDS_JQ
@pytest.mark.slow
@pytest.mark.parametrize(
    "file_path",
    [f"{WORKS}/a/README.md", f"{WORKS}/a/b/README.md"],
    ids=["a Work", "a Work below a Work"],
)
def test_the_hook_returns_the_errors_of_an_edit_of_a_contract(
    tmp_path: Path, file_path: str
) -> None:
    """AC-1: the command of the hook exits 2 with the diagnostics on stderr."""
    # Given the hook's command and a fake `uv` that prints the diagnostic of a
    # contract with an unknown dependency and exits 1

    # When the command receives the input for an edit of a contract, in the Works
    # directory and in a subdirectory of a Work
    code, out, err = _RUN(
        find_hook(CHECK), tmp_path, file_path, exit_code=1, output=DIAGNOSTIC
    )

    # Then it exits 2 with that diagnostic on standard error and nothing on
    # standard output, and the fake `uv` was called with `run wio contracts check`
    assert (code, out, err) == (2, "", f"{DIAGNOSTIC}\n")
    assert check_was_called(tmp_path)


@NEEDS_JQ
@pytest.mark.slow
@pytest.mark.parametrize(
    "file_path",
    [
        "/work/src/wio/cli/x.py",
        "/work/.agents/wio/config.toml",
        "/work/.agents/wio/templates/feature.leaf.md",
        f"{WORKS}/a/notes.txt",
        "/work/docs/README.md",
        ".agents/wio/works/a/README.md",
    ],
    ids=["source", "config", "template", "not Markdown", "outside", "relative"],
)
def test_the_hook_is_silent_when_the_edit_is_not_a_contract(
    tmp_path: Path, file_path: str
) -> None:
    """AC-2: a file that is not a contract prints nothing and calls no check."""
    # Given the hook's command and a fake `uv` for a check that fails

    # When the command receives the input for an edit of a source file, the config,
    # a template, a file of the Works directory that is not Markdown, a Markdown
    # file outside the Works directory and a path that is not absolute
    code, out, err = _RUN(
        find_hook(CHECK), tmp_path, file_path, exit_code=1, output=DIAGNOSTIC
    )

    # Then it exits 0 with no output, and the check was not called
    assert (code, out, err) == (0, "", "")
    assert not check_was_called(tmp_path)


@NEEDS_JQ
@pytest.mark.slow
@pytest.mark.parametrize(
    "output",
    ["The contracts pass.", "warning: .agents/wio/works/a/README.md: A warning"],
    ids=["the contracts pass", "a warning alone"],
)
def test_the_hook_is_silent_for_a_check_that_passes(
    tmp_path: Path, output: str
) -> None:
    """AC-2: a passing check, and one that only warns, print nothing."""
    # Given the hook's command and a fake `uv` for a check that exits 0 with the
    # message of a pass, and with a warning

    # When the command receives the input for an edit of a contract
    code, out, err = _RUN(
        find_hook(CHECK), tmp_path, f"{WORKS}/a/README.md", exit_code=0, output=output
    )

    # Then it ran the check and exits 0 with no output
    assert check_was_called(tmp_path)
    assert (code, out, err) == (0, "", "")


@NEEDS_JQ
@pytest.mark.slow
@pytest.mark.parametrize("check_exit", [2, 127], ids=["refused", "not found"])
def test_the_hook_does_not_block_an_edit_when_the_check_cannot_run(
    tmp_path: Path, check_exit: int
) -> None:
    """AC-3: a check that exits with anything but 1 gives exit 0 and no output."""
    # Given the hook's command and a fake `uv` for a check that exits 2, as a
    # config with an error makes the real one, and one that exits 127

    # When the command receives the input for an edit of a contract
    code, out, err = _RUN(
        find_hook(CHECK),
        tmp_path,
        f"{WORKS}/a/README.md",
        exit_code=check_exit,
        output=DIAGNOSTIC,
    )

    # Then it ran the check and exits 0 with no output
    assert check_was_called(tmp_path)
    assert (code, out, err) == (0, "", "")


def test_prek_runs_the_check_when_a_contract_is_in_the_commit() -> None:
    """AC-4: the hook matches the Works directory and passes no file names."""
    # Given `prek.toml`
    prek = tomllib.loads((ROOT / "prek.toml").read_text())

    # When its hook for the contracts is read
    hooks = [
        hook
        for repo in prek["repos"]
        for hook in repo["hooks"]
        if hook["id"] == "wio-contracts"
    ]

    # Then it runs `uv run wio contracts check`, matches a `.md` file in any
    # subdirectory of the Works directory and no other path, the same directory
    # inside a fixture included, and passes no file names
    assert len(hooks) == 1
    hook = hooks[0]
    assert hook["entry"] == CHECK
    assert hook["pass_filenames"] is False
    pattern = hook["files"]
    matched = [
        ".agents/wio/works/a/README.md",
        ".agents/wio/works/a/b/c/README.md",
    ]
    others = [
        "src/wio/cli/x.py",
        ".agents/wio/config.toml",
        ".agents/wio/templates/feature.leaf.md",
        ".agents/wio/works/a/notes.txt",
        "tests/fixtures/contracts/check-clean/.agents/wio/works/a/README.md",
    ]
    assert all(re.search(pattern, path) for path in matched)
    assert not any(re.search(pattern, path) for path in others)


@NEEDS_GIT
@pytest.mark.slow
def test_a_commit_that_changes_a_contract_with_an_error_is_refused(
    tmp_path: Path,
) -> None:
    """AC-4: `prek` fails the hook and prints the diagnostic of the check."""
    # Given a git repository with this repository's hook, a minimal config, and a
    # staged contract whose `depends_on` names an id that no Work has
    files = {
        ".agents/wio/config.toml": CONFIG.read_text(),
        ".agents/wio/works/a/README.md": BROKEN,
    }

    # When `prek` runs the hook on the staged files
    code, output = run_prek(tmp_path, files, "wio-contracts")

    # Then the hook fails and prints the diagnostic that names the unknown
    # dependency
    assert code != 0
    assert "wio contracts check" in output
    assert "Failed" in output
    assert DIAGNOSTIC in output


@NEEDS_GIT
@pytest.mark.slow
def test_a_commit_with_no_contract_does_not_run_the_hook(tmp_path: Path) -> None:
    """AC-4: the hook is skipped when no contract is staged."""
    # Given a git repository in which only a source file is staged, beside a
    # config
    files = {
        ".agents/wio/config.toml": CONFIG.read_text(),
        "src/wio/cli/x.py": "x = 1\n",
    }

    # When `prek` runs the hook on the staged files
    code, output = run_prek(tmp_path, files, "wio-contracts")

    # Then its output marks the hook `(no files to check)Skipped`
    assert code == 0
    assert "(no files to check)Skipped" in output
