# SPDX-License-Identifier: Apache-2.0
"""Tests of what a fresh interpreter loads when `wio config` is described and run."""

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from tests.support import git, import_light_violations

if TYPE_CHECKING:
    from tests.sandbox import Sandbox


@pytest.mark.slow
def test_describing_the_command_loads_no_submodule_of_the_package() -> None:
    """AC-5: the table of commands is described without the implementation."""
    # Given a new Python process

    # When the table of commands is described
    found = import_light_violations("wio.config")

    # Then no submodule of `wio.config` is in `sys.modules`
    assert found == []


@pytest.mark.slow
def test_listing_the_settings_does_not_load_json(sandbox: Sandbox) -> None:
    """Only `--json` imports the `json` module."""
    # Given a repository with a valid config and a fresh interpreter
    git(sandbox, "init", "--quiet", check=True)
    config = sandbox.root / ".agents" / "wio" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text("", encoding="utf-8")
    code = (
        "import sys\n"
        "from wio import cli\n"
        "from wio.io.adapters import SystemStdio\n"
        "cli.main(['config', 'list'], SystemStdio())\n"
        "sys.stderr.write(str('json' in sys.modules))\n"
    )

    # When the settings are listed in it
    done = subprocess.run(
        [sys.executable, "-c", code],
        cwd=sandbox.root,
        env=sandbox.env,
        capture_output=True,
        text=True,
        check=True,
    )

    # Then json was never imported
    assert done.stderr == "False"
    assert "trailers.reader" in done.stdout


@pytest.mark.slow
def test_checking_a_valid_config_loads_no_rarely_used_module(sandbox: Sandbox) -> None:
    """AC-2: a run with no problem imports neither `tomlkit`, `json` nor `difflib`."""
    # Given a repository with a valid config and a fresh interpreter
    git(sandbox, "init", "--quiet", check=True)
    config = sandbox.root / ".agents" / "wio" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text('[works]\nhierarchy = "nesting"\n', encoding="utf-8")
    code = (
        "import sys\n"
        "from wio import cli\n"
        "from wio.io.adapters import SystemStdio\n"
        "code = cli.main(['config', 'check'], SystemStdio())\n"
        "names = ['tomlkit', 'json', 'difflib']\n"
        "sys.stderr.write(repr((code, [n for n in names if n in sys.modules])))\n"
    )

    # When `wio config check` runs through `main` in it
    done = subprocess.run(
        [sys.executable, "-c", code],
        cwd=sandbox.root,
        env=sandbox.env,
        capture_output=True,
        text=True,
        check=True,
    )

    # Then it passed, and none of the three modules is in `sys.modules`
    assert done.stdout == "Config check passed!\n"
    assert done.stderr == "(0, [])"
