# SPDX-License-Identifier: Apache-2.0
"""Tests of the sandbox of the acceptance test drivers against real git."""

from typing import TYPE_CHECKING

import pytest

from tests.sandbox import Sandbox
from tests.support import git

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.slow
def test_git_in_the_sandbox_reads_nothing_from_the_developer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Global config, a repository above and a redirect have no effect."""
    # Given a home with a global git config and ignore file, a repository
    # that contains the temporary directory, and a git hook's GIT_DIR
    home = tmp_path / "home"
    (home / ".config" / "git").mkdir(parents=True)
    (home / ".gitconfig").write_text("[user]\n\tname = Leak\n", encoding="utf-8")
    (home / ".config" / "git" / "ignore").write_text("*\n", encoding="utf-8")
    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    setup = Sandbox.under(tmp_path / "setup")
    git(setup, "init", "-q", str(outer), check=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_DIR", str(outer / ".git"))
    sandbox = Sandbox.under(inner)

    # When git runs in the sandbox
    name = git(sandbox, "config", "user.name")
    toplevel = git(sandbox, "rev-parse", "--show-toplevel")
    git(sandbox, "init", "-q")
    (sandbox.root / "a.txt").write_text("a", encoding="utf-8")
    status = git(sandbox, "status", "--porcelain")

    # Then it has no global config, no repository above, and no global ignore
    assert name.returncode == 1
    assert toplevel.returncode != 0
    assert status.stdout.strip() == "?? a.txt"
