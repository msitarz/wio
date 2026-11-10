# SPDX-License-Identifier: Apache-2.0
"""Tests that this repository's templates are named by their files."""

import hashlib
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / ".agents" / "wio" / "templates"
SCRIPT = Path(sys.executable).parent / "wio"
NAMES = ("feature.draft", "feature.leaf", "feature.parent")


def test_the_repository_lists_its_templates_by_their_files() -> None:
    """AC-7: `wio templates list` names the three `feature` templates."""
    # Given the delivered tree

    # When `wio templates list` runs in it
    done = subprocess.run(
        [str(SCRIPT), "templates", "list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then it lists the three under `feature`, the draft marked as the entry
    lines = done.stdout.splitlines()
    names = [
        line.split()[0] for line in lines if line.startswith("  ") and line[2] != " "
    ]
    assert lines[0] == "feature"
    assert lines[1].split()[:2] == ["feature.draft", "[entry]"]
    assert names == list(NAMES)
    assert (done.returncode, done.stderr) == (0, "")


@pytest.mark.parametrize("name", NAMES)
def test_a_template_of_the_repository_has_no_name_key(name: str) -> None:
    """AC-7: the file names the template, so its block has no `name` key."""
    # Given the block of a template of this repository
    text = (TEMPLATES / f"{name}.md").read_text(encoding="utf-8")
    block = text.removeprefix("<!-- wio\n").split("\n-->\n", maxsplit=1)[0]

    # When the block is read as TOML
    data = tomllib.loads(block)

    # Then it has no `name` key
    assert "name" not in data


def _wio(*arguments: str) -> tuple[str, str, int]:
    """Run `wio templates` in this repository.

    Args:
        *arguments: The arguments after `wio templates`.

    Returns:
        Standard output, standard error and the exit code.
    """
    done = subprocess.run(
        [str(SCRIPT), "templates", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return done.stdout, done.stderr, done.returncode


def test_the_repository_lists_the_feature_kind_with_its_entry() -> None:
    """Parent AC-3: `list --kind feature` shows the three, the draft as the entry."""
    # Given this repository

    # When `wio templates list --kind feature` runs
    out, err, code = _wio("list", "--kind", "feature")

    # Then it lists `feature.draft` marked `[entry]`, `feature.leaf` and
    # `feature.parent`
    lines = out.splitlines()
    names = [line.split()[0] for line in lines if line.startswith("  ")]
    assert lines[1].split()[:2] == ["feature.draft", "[entry]"]
    assert [name for name in names if name.startswith("feature.")] == list(NAMES)
    assert (err, code) == ("", 0)


def test_the_skeleton_of_the_parent_template_has_no_template_only_keys() -> None:
    """Parent AC-3: no `name`, `kind`, `shape`, `description`, `[actions]` or list."""
    # Given this repository

    # When `wio templates show feature.parent` runs
    out, err, code = _wio("show", "feature.parent")

    # Then its block has no `name`, `kind`, `shape`, `description` or `actions`,
    # its body has no directive comment, and nothing else is written
    block = out.removeprefix("<!-- wio\n").split("\n-->\n", maxsplit=1)[0]
    keys = set(tomllib.loads(block))
    assert keys.isdisjoint({"name", "kind", "shape", "description", "actions"})
    assert "template" in keys
    assert "<!-- wio:" not in out
    assert (err, code) == ("", 0)


def test_the_repository_templates_pass_the_check() -> None:
    """Parent AC-3: `wio templates check` passes on this repository."""
    # Given this repository

    # When `wio templates check` runs
    out, err, code = _wio("check")

    # Then it passes
    assert (out, err, code) == ("The templates pass.\n", "", 0)


def _hashes() -> dict[str, str]:
    """Hash every file of the templates directory.

    Returns:
        The SHA-256 of each file, by its path relative to the directory.
    """
    return {
        str(path.relative_to(TEMPLATES)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(TEMPLATES.rglob("*"))
        if path.is_file()
    }


def test_no_command_changes_a_template() -> None:
    """Parent AC-3: `list`, `show` and `check` leave every template as it was."""
    # Given this repository's templates and a hash of each file
    before = _hashes()

    # When `wio templates list`, `show` and `check` run on them
    for arguments in (("list",), ("show", "feature.parent"), ("check",)):
        _wio(*arguments)

    # Then the hash of every template is unchanged
    assert before
    assert _hashes() == before


@pytest.mark.parametrize(
    "arguments",
    [("list",), ("show", "feature.parent"), ("check",)],
    ids=["list", "show", "check"],
)
def test_a_command_prints_the_same_twice(arguments: tuple[str, ...]) -> None:
    """Parent AC-3: the output of each command is identical on every run."""
    # Given this repository's templates

    # When the command runs twice
    first = _wio(*arguments)
    second = _wio(*arguments)

    # Then the two outputs are identical
    assert first == second
