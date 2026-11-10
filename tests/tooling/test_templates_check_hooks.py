# SPDX-License-Identifier: Apache-2.0
"""Tests of the hooks that run `wio templates check` and the recipe that shows them."""

import re
import tomllib
from typing import TYPE_CHECKING

import pytest

from tests.tooling.hooks import NEEDS_JQ, ROOT, find_hook, run_hook

if TYPE_CHECKING:
    from pathlib import Path

CHECK = "uv run wio templates check"
TEMPLATES = "/work/.agents/wio/templates"
DIAGNOSTIC = "error: .agents/wio/templates/feature.leaf.md: Unknown key `x`"


def _run_hook(
    tmp_path: Path, file_path: str, check_exit: int, output: str = DIAGNOSTIC
) -> tuple[int, str, str]:
    """Run the command of the hook with a fake `uv` that stands for the check.

    Args:
        tmp_path: A directory for the fake `uv`.
        file_path: The path the hook's JSON names as the edited file, absolute as
            the harness gives it.
        check_exit: The exit code of the fake check.
        output: The line that the fake check prints on standard output.

    Returns:
        The exit code, standard output and standard error of the hook.
    """
    return run_hook(
        find_hook(CHECK),
        tmp_path,
        file_path,
        check="templates check",
        exit_code=check_exit,
        output=output,
    )


@NEEDS_JQ
@pytest.mark.slow
@pytest.mark.parametrize(
    "file_path",
    [f"{TEMPLATES}/feature.leaf.md", f"{TEMPLATES}/sub/other.md"],
    ids=["in the directory", "in a subdirectory"],
)
def test_the_hook_returns_the_errors_of_an_edit_of_a_template(
    tmp_path: Path, file_path: str
) -> None:
    """AC-1: the command of the hook exits 2 with the diagnostics on stderr."""
    # Given the hook's command, a fake `uv` that stands for a check that fails
    # (the template has an unknown key), and the `PostToolUse` input for an edit
    # of a template, in the directory and in a subdirectory

    # When the command runs with that input
    code, out, err = _run_hook(tmp_path, file_path, check_exit=1)

    # Then it exits 2 with the diagnostics on standard error and nothing on
    # standard output
    assert (code, out, err) == (2, "", f"{DIAGNOSTIC}\n")


@NEEDS_JQ
@pytest.mark.slow
@pytest.mark.parametrize(
    "file_path",
    [
        "/work/src/wio/cli/x.py",
        "/work/.agents/wio/config.toml",
        f"{TEMPLATES}/notes.txt",
    ],
    ids=["source", "config", "not Markdown"],
)
def test_the_hook_is_silent_when_the_edit_is_not_a_template(
    tmp_path: Path, file_path: str
) -> None:
    """AC-2: a file that is not a template prints nothing, whatever the check says."""
    # Given the hook's command and a fake `uv` for a check that fails

    # When the command receives the input for an edit of that file
    code, out, err = _run_hook(tmp_path, file_path, check_exit=1)

    # Then it exits 0 with no output
    assert (code, out, err) == (0, "", "")


@NEEDS_JQ
@pytest.mark.slow
@pytest.mark.parametrize(
    "output",
    ["The templates pass.", "warning: .agents/wio/templates/a.md:9: A repeat"],
    ids=["the templates pass", "a warning alone"],
)
def test_the_hook_is_silent_for_a_check_that_passes(
    tmp_path: Path, output: str
) -> None:
    """AC-2: a passing check, and one that only warns, print nothing."""
    # Given the hook's command and a fake `uv` for a check that exits 0 with the
    # message of a pass, and with a warning

    # When the command receives the input for an edit of a template
    code, out, err = _run_hook(
        tmp_path, f"{TEMPLATES}/feature.leaf.md", check_exit=0, output=output
    )

    # Then it exits 0 with no output, so the message of a pass is not printed
    assert (code, out, err) == (0, "", "")


@NEEDS_JQ
@pytest.mark.slow
@pytest.mark.parametrize("check_exit", [2, 70], ids=["refused", "crashed"])
def test_the_hook_does_not_block_an_edit_when_the_check_cannot_run(
    tmp_path: Path, check_exit: int
) -> None:
    """AC-3: a check that exits with anything but 1 gives exit 0 and no output."""
    # Given the hook's command and a fake `uv` for a check that exits 2, as a
    # config with an error makes the real one, and one that exits 70

    # When the command receives the input for an edit of a template
    code, out, err = _run_hook(
        tmp_path, f"{TEMPLATES}/feature.leaf.md", check_exit=check_exit
    )

    # Then it exits 0 with no output
    assert (code, out, err) == (0, "", "")


def test_prek_runs_the_check_when_a_template_is_in_the_commit() -> None:
    """AC-4: the hook matches the templates and passes them no file names."""
    # Given `prek.toml`
    prek = tomllib.loads((ROOT / "prek.toml").read_text())

    # When its hook for the templates is read
    hooks = [
        hook
        for repo in prek["repos"]
        for hook in repo["hooks"]
        if hook["id"] == "wio-templates"
    ]

    # Then it runs `uv run wio templates check`, matches a `.md` file in any
    # subdirectory of the templates directory and no other path, and passes no
    # file names, so a commit with no template does not run it
    assert len(hooks) == 1
    hook = hooks[0]
    assert hook["entry"] == CHECK
    assert hook["pass_filenames"] is False
    pattern = hook["files"]
    matched = [
        ".agents/wio/templates/feature.leaf.md",
        ".agents/wio/templates/sub/other.md",
    ]
    others = [
        "src/wio/cli/x.py",
        ".agents/wio/config.toml",
        ".agents/wio/templates/notes.txt",
        "tests/fixtures/templates/check-pass/.agents/wio/templates/feature.draft.md",
    ]
    assert all(re.search(pattern, path) for path in matched)
    assert not any(re.search(pattern, path) for path in others)


def _section_seven() -> str:
    """Read section 7 of `docs/workflow.md`, on one line.

    Returns:
        The text from its heading to the end of the file, whitespace collapsed.
    """
    text = (ROOT / "docs" / "workflow.md").read_text()
    return " ".join(text[text.index("\n## 7. ") :].split())


def test_the_workflow_describes_both_hooks() -> None:
    """AC-5: section 7 shows an entry and a `prek` hook for each check."""
    # Given `docs/workflow.md`

    # When its section 7 is read
    text = _section_seven()

    # Then it says that the config and the templates are checked after every edit
    # and before every commit that changes them, shows the `.claude/settings.json`
    # entry for each, names the `prek` hook of each, and says that each project
    # decides how its harness runs the checks
    assert "after every edit and before every commit" in text
    assert '"PostToolUse"' in text
    assert "uv run wio config check" in text
    assert "uv run wio templates check" in text
    assert "`wio-config` hook of `prek.toml`" in text
    assert "`wio-templates` hook of `prek.toml`" in text
    assert "each project decides how its harness runs" in text
