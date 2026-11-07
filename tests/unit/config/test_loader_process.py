# SPDX-License-Identifier: Apache-2.0
"""Tests of the loader that need a process: imports, and the real repository."""

import ast
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.support import enter, git
from wio.config import load_config
from wio.errors import ConfigurationError
from wio.io import adapters

if TYPE_CHECKING:
    from tests.sandbox import Sandbox

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skip(reason="stub of the architecture stage"),
]

ROOT = Path(__file__).resolve().parents[3]
HEAVY = ("difflib", "json", "tomlkit")

_PROBE = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from wio.config import load_config

class Repository:
    def root(self): return Path("/repo")

class Files:
    def read_text(self, path): return sys.argv[2]

before = [name for name in {names} if name in sys.modules]
load_config(Repository(), Files())
sys.stdout.write(repr([before, [n for n in {names} if n in sys.modules]]))
"""


def _imported(text: str) -> list[str]:
    """Run the loader on a config text in a fresh interpreter.

    Args:
        text: The content of the config file.

    Returns:
        The heavy modules that are in `sys.modules` after the load.
    """
    probe = _PROBE.format(names=list(HEAVY))
    done = subprocess.run(
        [sys.executable, "-I", "-c", probe, str(ROOT / "src"), text],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    before, after = ast.literal_eval(done.stdout)
    assert before == []
    names: list[str] = after
    return names


def test_a_valid_file_loads_without_the_heavy_modules() -> None:
    """AC-8: no difflib, json or tomlkit for a valid file; difflib for a typo."""
    # Given a new Python process and a valid config, and one with an unknown key

    # When load_config runs and sys.modules is read
    valid = _imported('[works]\nhierarchy = "nesting"\n')
    typo = _imported('[trailers]\nreaders = "git"\n')

    # Then none of the three is there for the first, and difflib is for the second
    assert valid == []
    assert typo == ["difflib"]


def test_the_config_is_found_from_a_subdirectory(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: the working directory is below the root of the repository."""
    # Given a repository whose config sets the hierarchy, and a subdirectory
    git(sandbox, "init", "-q", check=True)
    config = sandbox.root / ".agents" / "wio" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text('[works]\nhierarchy = "nesting"\n', encoding="utf-8")
    sub = sandbox.root / "sub"
    sub.mkdir()
    enter(sandbox, monkeypatch)
    monkeypatch.chdir(sub)

    # When load_config runs with the real adapters
    loaded = load_config(adapters.GitRepository(), adapters.LocalFileSystem())

    # Then the hierarchy is nesting
    assert loaded.config is not None
    assert loaded.config.works.hierarchy == "nesting"


def test_outside_a_repository_the_error_names_the_working_directory(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: no repository is a configuration error that names the directory."""
    # Given a directory outside any repository
    enter(sandbox, monkeypatch)

    # When load_config runs with the real adapters
    with pytest.raises(ConfigurationError) as caught:
        load_config(adapters.GitRepository(), adapters.LocalFileSystem())

    # Then the error names the working directory and not wio init
    assert str(sandbox.root.resolve()) in str(caught.value)
    assert "wio init" not in str(caught.value)
