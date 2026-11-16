# SPDX-License-Identifier: Apache-2.0
"""Tests that this repository's own Works agree across the `contracts` commands.

They hold while the Works of `wio contracts` are delivered, and go with their
contracts when those are retired.
"""

import json
import subprocess

import pytest

from tests.tooling.own import ROOT, SCRIPT, hash_files

pytestmark = pytest.mark.slow

WORKS = ROOT / ".agents" / "wio" / "works"
PARENT = "912c07"
"""The id of the Work `wio contracts`, whose leaves are the Works nested below it."""


def _wio(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run `wio` in this repository.

    Args:
        *arguments: The arguments after `wio`.

    Returns:
        The finished process, whatever its exit code.
    """
    return subprocess.run(
        [str(SCRIPT), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _leaves() -> list[str]:
    """Find the ids of the Works that have the parent `wio contracts` as parent.

    Returns:
        The ids, in the order of `wio contracts list --json`.
    """
    works = json.loads(_wio("contracts", "list", "--json").stdout)
    return [work["id"] for work in works if work["parent"] == PARENT]


def test_the_repository_lists_shows_and_checks_its_own_works() -> None:
    """Parent AC-5: the Work with its leaves, a leaf with what it inherits."""
    # Given this repository
    leaves = _leaves()

    # When `wio contracts list`, `show <id of a leaf>` and `check` run in it
    listed = _wio("contracts", "list")
    shown = _wio("contracts", "show", leaves[0])
    checked = _wio("contracts", "check")

    # Then `list` shows this Work with its leaves nested below it, `show` prints
    # the leaf with this Work's Glossary and Constraints, and `check` passes
    lines = listed.stdout.splitlines()
    assert lines[0].startswith(f"{PARENT}  The wio contracts command")
    assert leaves
    assert all(any(line.startswith(f"  {leaf}  ") for line in lines) for leaf in leaves)
    assert "## Inherited from: The wio contracts command (912c07)" in shown.stdout
    assert "\n### Glossary\n" in shown.stdout
    assert "\n### Constraints\n" in shown.stdout
    assert (checked.stdout, checked.returncode) == ("The contracts pass.\n", 0)


def test_no_command_changes_a_contract() -> None:
    """Parent AC-5: `list`, `show`, `skeleton` and `check` change no contract."""
    # Given this repository's Works and a hash of each contract
    before = hash_files(WORKS)
    leaf = _leaves()[0]

    # When `list`, `show`, `skeleton feature.parent --work <leaf>` and `check` run
    codes = [
        _wio("contracts", *arguments).returncode
        for arguments in (
            ("list",),
            ("show", leaf),
            ("skeleton", "feature.parent", "--work", leaf),
            ("check",),
        )
    ]

    # Then each succeeded and the hash of every contract is unchanged
    assert codes == [0, 0, 0, 0]
    assert before
    assert hash_files(WORKS) == before


@pytest.mark.parametrize("command", ["list", "show", "check"])
def test_a_command_prints_the_same_twice(command: str) -> None:
    """Parent AC-5: the output of each command is identical on every run."""
    # Given this repository's Works
    arguments = ("show", _leaves()[0]) if command == "show" else (command,)

    # When the command runs twice
    first = _wio("contracts", *arguments)
    second = _wio("contracts", *arguments)

    # Then the two outputs are identical
    assert (first.stdout, first.stderr) == (second.stdout, second.stderr)
