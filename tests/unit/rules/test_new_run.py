# SPDX-License-Identifier: Apache-2.0
"""Tests of the steps of `wio rules new` over an in-memory repository."""

import io
import json
from argparse import Namespace
from typing import TYPE_CHECKING

import pytest

from tests.fakes import FakeEnvironment
from tests.unit.fakes import ROOT, FakeRepository, FakeStdio, MemoryFileSystem
from tests.unit.rules.support import Roots, Settings
from wio.errors import DiagnosticsError, WioError
from wio.models.config import Config, Root, Ruleset, Stage
from wio.models.frozen import freeze
from wio.rules import Services
from wio.rules.creating import run_new

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

_DEMO = ROOT / ".agents" / "wio" / "rules" / "demo"
_MANIFEST = (
    '[families]\nARC = "A"\nPAY = "P"\n'
    '[rule_presets.recommended]\nrules_include = ["ARC"]\n'
)


def _rule(code: str, name: str, extra: str = "") -> str:
    """Write a rule file.

    Args:
        code: The rule's code.
        name: The rule's name.
        extra: Lines for the block after the name.

    Returns:
        The text of the file.
    """
    return f'<!-- wio\ncode = "{code}"\nname = "{name}"\n{extra}-->\n\nBody.\n'


def _files(extra: Mapping[Path, str] | None = None) -> dict[Path, str]:
    """Write the repository of the examples.

    Args:
        extra: Further files, or files that replace these.

    Returns:
        `demo` with `ARC001` to `ARC003` and a rule preset `recommended`.
    """
    base = {_DEMO / "ruleset.toml": _MANIFEST}
    for number in (1, 2, 3):
        code = f"ARC00{number}"
        base[_DEMO / f"{code}-rule-{number}.md"] = _rule(code, f"rule-{number}")
    return {**base, **(extra or {})}


def _config() -> Config:
    """Build the config of AC-9: a root, a stage and an alias.

    Returns:
        The root `api` with `demo.recommended`, the stage `s` that includes
        `demo.ARC`, and the alias `d` for `demo`.
    """
    return Config(
        roots=freeze({"api": Root(("src",), ("demo.recommended",))}),
        stages=freeze({"s": Stage(goal="g", rules_include=("demo.ARC",))}),
        rulesets=freeze({"demo": Ruleset(alias="d")}),
    )


def _run(
    disk: MemoryFileSystem,
    *args: str,
    description: str | None = None,
    as_json: bool = False,
) -> FakeStdio:
    """Run `wio rules new` for a ruleset, a family and a name.

    Args:
        disk: The files of the repository.
        *args: The ruleset, the family and the name.
        description: The `--description` argument.
        as_json: Whether `--json` is given.

    Returns:
        The streams.
    """
    ruleset, family, name = args
    services = Services(
        Settings(_config()),
        FakeRepository(),
        disk,
        FakeEnvironment(ROOT),
        Roots({}),
    )
    given = Namespace(
        ruleset=ruleset, family=family, name=name, description=description, json=as_json
    )
    streams = FakeStdio()
    assert run_new(services, given, streams) == 0
    return streams


def _said(streams: FakeStdio) -> str:
    """Read what a run wrote to standard output.

    Args:
        streams: The streams of the run.

    Returns:
        The text.
    """
    assert isinstance(streams.stdout, io.StringIO)
    return streams.stdout.getvalue()


def test_it_creates_one_rule_and_says_what_selects_it() -> None:
    """AC-9: the lines of the result, and one new file."""
    # Given the repository, where the rule preset and the stage select `ARC`
    disk = MemoryFileSystem(_files())
    before = set(disk.files)

    # When the next rule of `ARC` is created
    streams = _run(disk, "demo", "ARC", "keep-it-small")

    # Then one file was written, and the result names the rule, the file and the
    # two origins
    path = ".agents/wio/rules/demo/ARC004-keep-it-small.md"
    assert set(disk.files) - before == {ROOT / path}
    assert _said(streams).splitlines() == [
        "created demo.ARC004 keep-it-small",
        f"file: {path}",
        "selected: demo.ARC004 ← root api ← demo.recommended ← demo.ARC",
        "selected: demo.ARC004 ← stage s ← demo.ARC",
    ]


def test_a_family_that_nothing_includes_is_not_selected_yet() -> None:
    """AC-9: `selected: no, nothing selects it yet`, in text and in JSON."""
    # Given the repository, where no entry includes `PAY`
    text = _run(MemoryFileSystem(_files()), "demo", "PAY", "pay-later")
    as_json = _run(MemoryFileSystem(_files()), "demo", "PAY", "pay-later", as_json=True)

    # Then the text says so, and the JSON has the fields in order and no origin
    assert _said(text).splitlines()[2] == ("selected: no, nothing selects it yet")
    found = json.loads(_said(as_json))
    assert list(found) == ["code", "name", "path", "selected", "origins"]
    assert (found["code"], found["selected"], found["origins"]) == (
        "demo.PAY001",
        False,
        [],
    )


def test_the_json_gives_the_origins_as_arrays_of_labels() -> None:
    """AC-10: one line, with `selected` true and the two chains."""
    # Given the repository
    # When the rule is created with `--json`
    streams = _run(MemoryFileSystem(_files()), "demo", "ARC", "x", as_json=True)

    # Then the document is one line with the chains of labels
    output = _said(streams)
    assert output.count("\n") == 1
    found = json.loads(output)
    assert found["selected"] is True
    assert found["origins"] == [
        ["root api", "demo.recommended", "demo.ARC"],
        ["stage s", "demo.ARC"],
    ]


def test_an_alias_is_accepted_and_the_canonical_name_is_shown() -> None:
    """AC-5: the file is in the ruleset's directory, and the code says `demo`."""
    # Given the repository, where `d` is the alias of `demo`
    disk = MemoryFileSystem(_files())

    # When the rule is created for `d`
    streams = _run(disk, "d", "ARC", "keep-it-small")

    # Then the result says `demo.ARC004` and the file is in the directory of `demo`
    assert _said(streams).startswith("created demo.ARC004 ")
    assert _DEMO / "ARC004-keep-it-small.md" in disk.files


def test_a_file_that_exists_is_refused_and_nothing_is_written() -> None:
    """AC-6: an unmarked file in the way is not overwritten."""
    # Given an unmarked file `ARC004-other.md`, which the next code would use
    extra = {_DEMO / "ARC004-other.md": "Not a rule.\n"}
    disk = MemoryFileSystem(_files(extra))
    before = dict(disk.files)

    # When the rule is created with the name `other`
    # Then it is refused with the file named and nothing is changed
    with pytest.raises(WioError) as raised:
        _run(disk, "demo", "ARC", "other")
    assert "ARC004-other.md" in str(raised.value)
    assert disk.files == before


def test_a_fault_in_another_ruleset_refuses_the_command() -> None:
    """AC-7: an error anywhere in the discovery, and no file is written."""
    # Given a ruleset `bad` with a rule whose block does not close
    bad = ROOT / ".agents" / "wio" / "rules" / "bad"
    extra = {bad / "ruleset.toml": "", bad / "ARC001-open.md": "<!-- wio\n"}
    disk = MemoryFileSystem(_files(extra))
    before = dict(disk.files)

    # When a rule is created in `demo`
    # Then the error is raised and nothing is written
    with pytest.raises(DiagnosticsError):
        _run(disk, "demo", "ARC", "keep-it-small")
    assert disk.files == before


def test_a_warning_refuses_nothing() -> None:
    """AC-8: a rule with an unknown key does not stop the command."""
    # Given a rule whose block has an unknown key
    extra = {_DEMO / "ARC001-rule-1.md": _rule("ARC001", "rule-1", 'owner = "me"\n')}
    disk = MemoryFileSystem(_files(extra))

    # When a rule is created
    streams = _run(disk, "demo", "ARC", "keep-it-small")

    # Then it is created
    assert _said(streams).startswith("created demo.ARC004 ")


def test_the_same_request_writes_the_same_bytes() -> None:
    """AC-11: the same path and text on two copies, and only one new file."""
    # Given two copies of one repository
    one, two = MemoryFileSystem(_files()), MemoryFileSystem(_files())

    # When the same request runs on each
    _run(one, "demo", "ARC", "keep-it-small", description="One line.")
    _run(two, "demo", "ARC", "keep-it-small", description="One line.")

    # Then they hold the same files with the same bytes
    assert one.files == two.files
    assert len(one.files) == len(_files()) + 1
