# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio templates directives`, which prints the directive grammar."""

from contextlib import contextmanager, nullcontext
from json import loads
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

NAMES = ["required", "items", "pattern", "inherit"]
SECTIONS = ["directives:", *NAMES, "combining:", "several directives"]
EXPECTED = """\
directives:

required
  Syntax: required
  The heading is present in the contract.
  Example: ## Purpose <!-- wio: required -->

items
  Syntax: items>=N
  The section holds at least N items, N being 1 or more.
  Example: ## Goals <!-- wio: items>=1 -->

pattern
  Syntax: pattern=<regex> or pattern="<regex>"
  The items of the section match the regular expression, and the matches are \
their item ids.
  Example: ## Acceptance criteria <!-- wio: pattern=AC-\\d+ -->
  Example: ## Acceptance criteria <!-- wio: pattern="AC-\\d{1,3}" -->

inherit
  Syntax: inherit
  A descendant's resolved view includes the section.
  Example: ## Glossary <!-- wio: inherit -->

combining:

several directives
  Syntax: <!-- wio: <directive>, <directive>, ... -->
  Write them in one comment at the end of the heading, separated by commas. \
All of them apply to the section. A heading has one such comment, and each \
directive is named once.
  Example: ## Acceptance criteria <!-- wio: required, items>=1, pattern=AC-\\d+ -->
"""


def _names(text: str) -> list[str]:
    """Pick the names of the blocks out of the listing.

    Args:
        text: What `wio templates directives` printed.

    Returns:
        The lines that start in the first column, which are the entries' names.
    """
    return [line for line in text.splitlines() if line and not line.startswith(" ")]


def _blocks(text: str) -> list[str]:
    """Pick the blocks of entries out of the listing.

    Args:
        text: What `wio templates directives` printed.

    Returns:
        The paragraphs that are not a section header.
    """
    return [b for b in text.split("\n\n") if not b.endswith(":\n") and "\n" in b[:-1]]


def _is_well_formed(block: str) -> bool:
    """Tell whether a block has the shape of an entry.

    Args:
        block: One paragraph of the listing.

    Returns:
        Whether the second line is the syntax, every line after the name is
        indented by two spaces, and an example line is there.
    """
    lines = block.splitlines()
    return (
        lines[1].startswith("  Syntax: ")
        and all(line.startswith("  ") for line in lines[1:])
        and any(line.startswith("  Example: ") for line in lines)
    )


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_directives_prints_the_directives_and_how_they_combine(wio: Wio) -> None:
    """AC-1: a `directives:` section, then a `combining:` section, exit 0."""
    # Given any working directory, the table and the entry for combining
    wio.fixture("templates/no-config")

    # When `wio templates directives` runs
    output = wio.run(["templates", "directives"])

    # Then it prints the two sections in order, with a block for each entry, empty
    # standard error, and exits 0
    assert _names(output.stdout) == SECTIONS
    blocks = _blocks(output.stdout)
    assert len(blocks) == len(NAMES) + 1
    assert all(_is_well_formed(block) for block in blocks)
    assert output.stdout.endswith("\n")
    assert not output.stdout.endswith("\n\n")
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_directives_json_prints_the_same_as_one_object(wio: Wio) -> None:
    """AC-2: `--json` prints one object with the two sections as arrays."""
    # Given any working directory, the table and the entry for combining
    wio.fixture("templates/no-config")

    # When `wio templates directives --json` runs
    output = wio.run(["templates", "directives", "--json"])

    # Then the output is one object with the keys `directives` and `combining` in
    # that order, an object for each entry in the table's order, one for
    # combining, empty standard error, and exit 0
    found = loads(output.stdout)
    assert list(found) == ["directives", "combining"]
    assert [item["name"] for item in found["directives"]] == NAMES
    assert [item["name"] for item in found["combining"]] == ["several directives"]
    for item in (*found["directives"], *found["combining"]):
        assert list(item) == ["name", "syntax", "meaning", "examples"]
        assert isinstance(item["examples"], list)
        assert item["examples"]
    assert (output.stderr, output.exit_code) == ("", 0)


@contextmanager
def _unreadable(directory: Path) -> Generator[None]:
    """Make a directory unreadable for the length of a block.

    Args:
        directory: The directory to close.

    Yields:
        Nothing, while the directory cannot be read.
    """
    directory.chmod(0o000)
    try:
        yield
    finally:
        directory.chmod(0o755)


@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize(
    "fixture",
    [None, "config/invalid", "templates/no-config", "templates/shown"],
    ids=["no-repository", "bad-config", "no-config", "unreadable-templates"],
)
def test_directives_works_outside_a_repository_and_with_a_broken_project(
    wio: Wio, sandbox: Sandbox, fixture: str | None
) -> None:
    """AC-3: the same output with no repository, a bad config or no templates."""
    # Given a directory outside any repository, a repository whose config has an
    # error, one with no config file and one whose templates directory is
    # unreadable
    if fixture is not None:
        wio.fixture(fixture)
    closed = fixture == "templates/shown"

    # When `wio templates directives` runs in it, with and without `--json`
    with (
        _unreadable(sandbox.root / ".agents/wio/templates") if closed else nullcontext()
    ):
        text = wio.run(["templates", "directives"])
        machine = wio.run(["templates", "directives", "--json"])

    # Then it prints the same text as anywhere else, with empty standard error,
    # and exits 0
    assert text.stdout == EXPECTED
    assert [i["name"] for i in loads(machine.stdout)["directives"]] == NAMES
    assert (text.stderr, text.exit_code) == ("", 0)
    assert (machine.stderr, machine.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_directives_prints_the_same_text_on_every_run(wio: Wio) -> None:
    """AC-7: each form is identical twice."""
    # Given any working directory
    wio.fixture("templates/no-config")

    # When `directives` and `directives --json` each run twice
    runs = {
        form: [wio.run(["templates", "directives", *form]) for _ in range(2)]
        for form in ((), ("--json",))
    }

    # Then the two outputs of each command are identical
    for first, second in runs.values():
        assert first == second


@pytest.mark.channels(Channel.CLI)
def test_directives_with_an_extra_argument_is_a_usage_mistake(wio: Wio) -> None:
    """AC-5: `directives extra` exits 2, and the help of `wio templates` names it."""
    # Given any working directory
    wio.fixture("templates/no-config")

    # When `wio templates directives extra` runs, and then `wio templates`
    wrong = wio.run(["templates", "directives", "extra"])
    help_output = wio.run(["templates"])
    directives_help = wio.run(["templates", "directives", "--help"])

    # Then the first exits 2 with a usage message, and the help names `directives`
    assert (wrong.exit_code, wrong.stdout) == (2, "")
    assert "usage:" in wrong.stderr
    assert "directives" in help_output.stdout
    assert directives_help.exit_code == 0
    assert "separated by commas" in " ".join(directives_help.stdout.split())
