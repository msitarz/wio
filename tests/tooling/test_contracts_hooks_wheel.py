# SPDX-License-Identifier: Apache-2.0
"""Tests that the real hooks of `wio contracts check` run the built wheel."""

import shlex
import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest

from tests.tooling.hooks import NEEDS_JQ, ROOT, find_hook, run_hook, run_prek

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.slow

CHECK = "uv run wio contracts check"
CONFIG = ROOT / "tests/fixtures/contracts/check-clean/.agents/wio/config.toml"
NEEDS_GIT = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
WORK = ".agents/wio/works/a/README.md"
VALID = '<!-- wio\nid = "hok001"\n-->\n\n# Title\n'
BROKEN = '<!-- wio\nid = "hok001"\ndepends_on = ["zzzzzz"]\n-->\n\n# Title\n'
DIAGNOSTIC = f"error: {WORK}: The dependency `zzzzzz` is not a Work"


@pytest.fixture(scope="module")
def wio(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Build the wheel and name the shell command that runs it.

    Args:
        tmp_path_factory: Makes the directory that the wheel is built into.

    Returns:
        A shell command that runs `wio` from the wheel alone, as the packaging
        tests do, so a hook that runs it exercises what a user installs.
    """
    out = tmp_path_factory.mktemp("dist")
    uv = shutil.which("uv")
    assert uv, "uv is required to build the package"
    subprocess.run(
        [uv, "build", "--wheel", "--out-dir", str(out)],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    [wheel] = out.glob("*.whl")
    return shlex.join(
        [uv, "run", "--no-project", "--isolated", "--with", str(wheel), "wio"]
    )


def _repository(tmp_path: Path, work: str) -> Path:
    """Make a repository that holds a config and one Work.

    Args:
        tmp_path: A directory of the test.
        work: The text of the Work `a`.

    Returns:
        The repository's root.
    """
    root = tmp_path / "project"
    (root / ".agents/wio/works/a").mkdir(parents=True)
    (root / ".agents/wio/config.toml").write_text(CONFIG.read_text())
    (root / WORK).write_text(work)
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    return root


@NEEDS_JQ
def test_the_hook_of_an_edit_runs_the_installed_check(tmp_path: Path, wio: str) -> None:
    """Parent AC-9: an edit of a contract fails with the diagnostic, or is silent."""
    # Given a repository with this repository's hook, a minimal config and a Work,
    # and a `uv` shim that runs the built wheel
    hook = find_hook(CHECK)
    broken = _repository(tmp_path / "broken", BROKEN)
    valid = _repository(tmp_path / "valid", VALID)

    # When the command of the hook receives the input for an edit of the Work, once
    # when the Work lists an id that no Work has and once when it does not
    def run(root: Path) -> tuple[int, str, str]:
        return run_hook(
            hook,
            root,
            str(root / WORK),
            check="",
            exit_code=0,
            output="",
            wio=wio,
            cwd=root,
        )

    refused, silent = run(broken), run(valid)

    # Then with the unknown dependency it exits 2 with the diagnostic on standard
    # error, and without it it prints nothing and exits 0
    assert refused[0] == 2
    assert DIAGNOSTIC in refused[2]
    assert silent == (0, "", "")


@NEEDS_GIT
def test_the_hook_of_a_commit_runs_the_installed_check(
    tmp_path: Path, wio: str
) -> None:
    """Parent AC-9: `prek` fails the hook with the diagnostic, or passes it."""
    # Given a repository with this repository's `prek.toml`, a minimal config and a
    # staged Work, and a `uv` shim that runs the built wheel
    config = CONFIG.read_text()
    broken, valid = tmp_path / "broken", tmp_path / "valid"
    broken.mkdir()
    valid.mkdir()

    # When `prek` runs the hook, once when the Work lists an id that no Work has
    # and once when it does not
    refused = run_prek(
        broken,
        {".agents/wio/config.toml": config, WORK: BROKEN},
        "wio-contracts",
        wio=wio,
    )
    passed = run_prek(
        valid,
        {".agents/wio/config.toml": config, WORK: VALID},
        "wio-contracts",
        wio=wio,
    )

    # Then with the unknown dependency the hook fails with the diagnostic, and
    # without it the hook passes
    assert refused[0] != 0
    assert DIAGNOSTIC in refused[1]
    assert passed[0] == 0
    assert "Passed" in passed[1]
