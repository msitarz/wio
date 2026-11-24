# SPDX-License-Identifier: Apache-2.0
"""System scenarios of `wio rules` as a whole: the criteria of its top Work."""

import json
import re
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.rules import support

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

_BOTH = pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
_FAMILIES = '[families]\nARC = "A"\nPAY = "P"\n'
_RECOMMENDED = '[rule_presets.recommended]\nrules_include = ["ARC"]\n'
_VIEW = ["--work", support.WORK, "--stage", "s"]


def _repo(wio: Wio, *, pay: bool = False, config: str = "") -> None:
    """Start the repository of AC-1: `demo` with `ARC001`, a root, a Work, a stage.

    Args:
        wio: The facade.
        pay: Whether the manifest declares the family `PAY` too.
        config: Text to add to the config, such as an alias.
    """
    wio.fixture(support.BASE)
    text = (
        '[roots.api]\npaths = ["src/api"]\nrule_presets = ["demo.recommended"]\n'
        '[stages.s]\ngoal = "g"\n'
    )
    wio.put(".agents/wio/config.toml", (text + config).encode())
    manifest = (_FAMILIES if pay else '[families]\nARC = "A"\n') + _RECOMMENDED
    support.ruleset(wio, "demo", manifest, {"ARC001": "keep"})
    support.work(wio, support.WORK, 'roots = ["api"]\n')


@_BOTH
def test_a_new_rule_is_accepted_listed_and_selected_without_an_edit(wio: Wio) -> None:
    """AC-1: `check` accepts it, `new` says it is selected, `list` shows its root."""
    # Given a ruleset whose rule preset includes `ARC`, a root, a Work and a stage
    _repo(wio)

    # When a rule is created, checked and listed for the Work at the stage
    created = wio.run(["rules", "new", "demo", "ARC", "--name", "keep-it-small"])
    checked = wio.run(["rules", "check"])
    listed = wio.run(["rules", "list", *_VIEW])

    # Then `check` reports no error, `new` says the rule is selected and `list`
    # shows it with the root `api`
    assert checked.exit_code == 0
    assert "selected: demo.ARC002 ← root api" in created.stdout
    assert support.shown(listed)["demo.ARC002"] == "api"
    assert "demo.ARC002  keep-it-small" in listed.stdout


@_BOTH
def test_a_rule_that_nothing_selects_is_said_so_and_listed_apart(wio: Wio) -> None:
    """AC-1: `new` says nothing selects it and `check` prints no line about it."""
    # Given the repository, where a family `PAY` is in no rule preset
    _repo(wio, pay=True)

    # When a rule is created in `PAY`, and `list --not-selected` and `check` run
    created = wio.run(["rules", "new", "demo", "PAY", "--name", "pay-later"])
    apart = wio.run(["rules", "list", "--not-selected"])
    checked = wio.run(["rules", "check"])

    # Then `new` says nothing selects it, `list` shows it and `check` is silent
    assert "selected: no, nothing selects it yet" in created.stdout
    assert "demo.PAY001  pay-later" in apart.stdout
    assert (checked.exit_code, "PAY001" in checked.stdout) == (0, False)


@_BOTH
def test_a_reference_that_check_calls_dead_is_cut_by_the_roots_in_the_list(
    wio: Wio,
) -> None:
    """AC-4: `check` warns, `list` leaves the rule out and `--explain` says why."""
    # Given a ruleset `py` that no root reaches, a stage that includes `py.API001`
    # and a Work whose roots are `web`
    wio.fixture(support.BASE)
    config = (
        '[roots.web]\npaths = ["web"]\n'
        '[stages.s]\ngoal = "g"\nrules_include = ["py.API001"]\n'
    )
    wio.put(".agents/wio/config.toml", config.encode())
    support.ruleset(wio, "py", '[families]\nAPI = "A"\n', {"API001": "typed"})
    support.work(wio, support.WORK, 'roots = ["web"]\n')

    # When `check` runs, and `list` runs for the Work at the stage, plain and with
    # `--explain`
    checked = wio.run(["rules", "check"])
    plain = wio.run(["rules", "list", *_VIEW])
    explained = wio.run(["rules", "list", "--explain", *_VIEW])

    # Then `check` warns of the reference, the plain listing does not apply the
    # rule and `--explain` says that the roots cut it
    assert "`py` is not root-independent" in checked.stdout
    assert "py.API001" not in plain.stdout
    assert "out: cut by the roots" in explained.stdout


def _narrowing_repo(wio: Wio) -> None:
    """Start the repository of AC-5.

    Args:
        wio: The facade.
    """
    wio.fixture(support.BASE)
    config = (
        '[roots.api]\npaths = ["src/api"]\nrule_presets = ["demo.all"]\n'
        '[stages.s]\ngoal = "g"\nrules_include = ["demo.ARC"]\n'
    )
    wio.put(".agents/wio/config.toml", config.encode())
    support.ruleset(
        wio,
        "demo",
        _FAMILIES,
        {"ARC001": "one", "ARC002": "two", "PAY001": "pay"},
    )
    support.work(wio, support.WORK, 'roots = ["api"]\n')


@_BOTH
@pytest.mark.parametrize(
    "view",
    [
        [],
        ["--root", "api"],
        ["--path", "src/api/app.py"],
        ["--stage", "s"],
        ["--work", support.WORK, "--stage", "s"],
    ],
    ids=["none", "root", "path", "stage", "work"],
)
def test_a_reference_narrows_every_view_of_a_listing(wio: Wio, view: list[str]) -> None:
    """AC-5: each view keeps the rules of `demo.ARC` and names the reference."""
    # Given a ruleset with two `ARC` rules and a `PAY` rule, all reached by a root
    _narrowing_repo(wio)

    # When `list demo.ARC` runs with the view
    output = wio.run(["rules", "list", "demo.ARC", *view])

    # Then it shows the two `ARC` rules, not the `PAY` rule, and names the reference
    assert list(support.shown(output)) == ["demo.ARC001", "demo.ARC002"]
    assert "references: demo.ARC" in support.header(output)


_ALIASED = (
    '[rulesets.demo]\nalias = "d"\n'
    '[stages.s]\ngoal = "g"\nrules_include = ["d.recommended"]\n'
)


def _aliased_repo(wio: Wio) -> None:
    """Start the repository of AC-6: `demo` with the alias `d`.

    Args:
        wio: The facade.
    """
    wio.fixture(support.BASE)
    config = '[roots.api]\npaths = ["src/api"]\nrule_presets = ["d.recommended"]\n'
    wio.put(".agents/wio/config.toml", (config + _ALIASED).encode())
    support.ruleset(
        wio, "demo", '[families]\nARC = "A"\n' + _RECOMMENDED, {"ARC001": "keep"}
    )
    support.work(wio, support.WORK, 'roots = ["api"]\n')


@_BOTH
@pytest.mark.parametrize(
    ("view", "layers"),
    [
        (["demo.recommended"], "none"),
        (["--root", "api"], "roots, always fields"),
        (["--path", "src/api/app.py"], "roots, always fields"),
        (["--stage", "s"], "stage, always fields"),
        (["--work", support.WORK, "--stage", "s"], "roots, stage, always fields"),
    ],
    ids=["references", "root", "path", "stage", "work"],
)
def test_one_rule_reaches_every_view_alike_by_its_canonical_code(
    wio: Wio, view: list[str], layers: str
) -> None:
    """AC-6: `demo.ARC001` with its name and summary, never `d.ARC001`."""
    # Given a ruleset with the alias `d` that a root, a stage and a Work select
    _aliased_repo(wio)

    # When `list` runs with the view
    output = wio.run(["rules", "list", *view])

    # Then the rule is shown by its canonical code, name and summary, and the
    # header names the layers
    assert "demo.ARC001  keep" in output.stdout
    assert "Body." in output.stdout
    assert "d.ARC001" not in output.stdout.replace("demo.ARC001", "")
    assert f"layers: {layers}" in support.header(output)


@_BOTH
def test_the_work_view_explains_the_root_and_the_rule_preset(wio: Wio) -> None:
    """AC-6: `--explain` names the root `api` and the rule preset `demo.recommended`."""
    # Given the repository of AC-6
    _aliased_repo(wio)

    # When the Work at the stage is listed with `--explain`
    output = wio.run(["rules", "list", "--explain", *_VIEW])

    # Then the origins name the root and the rule preset
    assert "root api" in output.stdout
    assert "demo.recommended" in output.stdout


def _formats_repo(wio: Wio) -> None:
    """Start the repository of AC-7: both forms of a rule file.

    Args:
        wio: The facade.
    """
    wio.fixture(support.BASE)
    config = (
        '[roots.api]\npaths = ["src/api"]\nrule_presets = ["demo.all"]\n'
        '[stages.s]\ngoal = "g"\n'
    )
    wio.put(".agents/wio/config.toml", config.encode())
    wio.put(f"{support.RULES}/demo/ruleset.toml", b'[families]\nARC = "A"\n')
    wio.put(
        f"{support.RULES}/demo/ARC001-comment.md",
        support.rule("ARC001", "comment", "One.\n"),
    )
    front = b'+++\nwio = 1\ncode = "ARC002"\nname = "front"\n+++\n\nTwo.\n'
    wio.put(f"{support.RULES}/demo/ARC002-front.md", front)
    wio.put(
        f"{support.RULES}/demo/notes.md", support.rule("ARC003", "noted", "Three.\n")
    )
    support.work(wio, support.WORK, 'roots = ["api"]\n')


@_BOTH
def test_a_rule_file_of_either_form_and_of_any_name_is_treated_alike(
    wio: Wio,
) -> None:
    """AC-7: checked, listed and shown alike, whatever the form or the file name."""
    # Given rules in the comment form, in `+++` form and in a file named `notes.md`
    _formats_repo(wio)

    # When `check`, `list` for the Work and `show` for each rule run
    checked = wio.run(["rules", "check"])
    listed = wio.run(["rules", "list", *_VIEW])
    shows = [wio.run(["rules", "show", f"demo.ARC00{n}"]) for n in (1, 2, 3)]

    # Then `check` reports no error, the three are listed alike and each is shown
    assert checked.exit_code == 0
    assert list(support.shown(listed)) == ["demo.ARC001", "demo.ARC002", "demo.ARC003"]
    assert [s.stdout.splitlines()[-1] for s in shows] == ["One.", "Two.", "Three."]


@_BOTH
def test_the_next_code_reads_a_rule_in_front_matter(wio: Wio) -> None:
    """AC-7: after `ARC003` in `+++` form, the new rule is `ARC004`."""
    # Given a ruleset whose highest rule has `+++` front matter
    wio.fixture(support.BASE)
    wio.put(f"{support.RULES}/demo/ruleset.toml", b'[families]\nARC = "A"\n')
    front = b'+++\nwio = 1\ncode = "ARC003"\nname = "front"\n+++\n\nBody.\n'
    wio.put(f"{support.RULES}/demo/ARC003-front.md", front)

    # When a rule is created in `ARC` of `demo`, and `check` runs
    created = wio.run(["rules", "new", "demo", "ARC", "--name", "next-one"])
    checked = wio.run(["rules", "check"])

    # Then the new rule is `ARC004` and `check` reports no error
    assert created.stdout.startswith("created demo.ARC004 next-one")
    assert checked.exit_code == 0


@_BOTH
def test_show_and_list_describe_a_rule_alike(wio: Wio) -> None:
    """AC-8: the description where there is one, else the summary."""
    # Given `ARC001` with a description and `ARC002` without one
    _repo(wio)
    described = support.rule(
        "ARC001", "keep", "Keep it small.\n", 'description = "Small."\n'
    )
    wio.put(f"{support.RULES}/demo/ARC001-keep.md", described)
    wio.put(
        f"{support.RULES}/demo/ARC002-name.md",
        support.rule("ARC002", "name", "Say it.\n"),
    )

    # When both are shown, and `demo.recommended` is listed
    first = wio.run(["rules", "show", "demo.ARC001"])
    second = wio.run(["rules", "show", "demo.ARC002"])
    listed = wio.run(["rules", "list", "demo.recommended"])

    # Then each `show` has the code, the name, the description if any, and the body,
    # and `list` has the description of the first and the summary of the second
    assert first.stdout.startswith("demo.ARC001  keep\n")
    assert "Small." in first.stdout
    assert first.stdout.endswith("\nKeep it small.\n")
    assert "Say it." in second.stdout
    assert "demo.ARC002  name\n             Say it.\n" in listed.stdout
    assert "demo.ARC001  keep\n             Small.\n" in listed.stdout


def _faulty(wio: Wio) -> None:
    """Add two rules with one code to the repository.

    Args:
        wio: The facade.
    """
    wio.put(f"{support.RULES}/demo/ARC002-one.md", support.rule("ARC002", "one"))
    wio.put(f"{support.RULES}/demo/ARC002-two.md", support.rule("ARC002", "two"))


@_BOTH
def test_a_fault_reaches_check_and_stops_the_other_commands(wio: Wio) -> None:
    """AC-9: `check` exits 1 naming both files; `new`, `list` and `show` exit 2."""
    # Given a ruleset with two rules with the code `ARC002`
    _repo(wio)
    _faulty(wio)
    before = wio.fingerprint(support.RULES)

    # When `check`, `new`, `list` and `show` run
    checked = wio.run(["rules", "check"])
    created = wio.run(["rules", "new", "demo", "ARC", "--name", "next-one"])
    listed = wio.run(["rules", "list", "demo.recommended"])
    shows = wio.run(["rules", "show", "demo.ARC001"])

    # Then `check` names both files and exits 1, the others exit 2 with the error on
    # standard error and nothing on standard output, and nothing was written
    assert checked.exit_code == 1
    assert "ARC002-one.md" in checked.stdout
    assert "ARC002-two.md" in checked.stdout
    for refused in (created, listed, shows):
        assert (refused.exit_code, refused.stdout) == (2, "")
        assert "ARC002-one.md" in refused.stderr
    assert wio.fingerprint(support.RULES) == before


@_BOTH
@pytest.mark.parametrize("faulty", [False, True], ids=["valid", "faulty"])
def test_check_list_and_show_write_nothing(wio: Wio, *, faulty: bool) -> None:
    """AC-11: every file of the repository is what it was."""
    # Given a repository with a valid ruleset, or with a faulty one
    _repo(wio)
    if faulty:
        _faulty(wio)
    before = wio.fingerprint(".")

    # When `check`, `list` and `show` run
    for args in (["check"], ["list"], ["show", "demo.ARC001"]):
        wio.run(["rules", *args])

    # Then every file is byte for byte what it was
    assert wio.fingerprint(".") == before


@_BOTH
def test_a_rule_that_nothing_selects_is_listed_and_not_warned_about(wio: Wio) -> None:
    """AC-12: `list --not-selected` shows them and `check` prints nothing about them."""
    # Given `ARC002` excluded by the rule preset and `PAY001` in no rule preset
    wio.fixture(support.BASE)
    config = '[roots.api]\npaths = ["src/api"]\nrule_presets = ["demo.recommended"]\n'
    wio.put(".agents/wio/config.toml", config.encode())
    manifest = _FAMILIES + _RECOMMENDED + 'rules_exclude = ["ARC002"]\n'
    support.ruleset(
        wio, "demo", manifest, {"ARC001": "one", "ARC002": "two", "PAY001": "pay"}
    )

    # When `list --not-selected` and `check` run
    listed = wio.run(["rules", "list", "--not-selected"])
    checked = wio.run(["rules", "check"])

    # Then the first shows `ARC002` and `PAY001` and not `ARC001`, and `check` is
    # silent about them and exits 0
    assert list(support.shown(listed)) == ["demo.ARC002", "demo.PAY001"]
    assert (checked.exit_code, checked.stdout) == (0, "The rules pass.\n")


def _order_config(*, reverse: bool) -> bytes:
    """Write the config of AC-3 with its tables and rule presets in one of two orders.

    Args:
        reverse: Whether the tables and the root's rule presets come in the
            opposite order.

    Returns:
        The text of the config.
    """
    step = -1 if reverse else 1
    presets = ", ".join(['"demo.all"', '"other.all"'][::step])
    includes = '"demo.all", "other.all", "demo.XYZ"'
    tables = [
        f'[roots.api]\npaths = ["src"]\nrule_presets = [{presets}]\n',
        f'[stages.s]\ngoal = "g"\nrules_include = [{includes}]\n',
    ]
    return "".join(tables[::step]).encode()


def _ordered_repo(wio: Wio) -> None:
    """Start the repository of AC-3.

    Args:
        wio: The facade.
    """
    wio.fixture(support.BASE)
    wio.put(".agents/wio/config.toml", _order_config(reverse=False))
    files = {
        "demo/ruleset.toml": b'[families]\nARC = "A"\nPAY = "P"\n',
        "demo/ARC001-one.md": support.rule("ARC001", "one"),
        "demo/ARC002-two.md": support.rule("ARC002", "two"),
        "demo/PAY001-pay.md": support.rule("PAY001", "pay"),
        "other/ruleset.toml": b'[families]\nARC = "A"\nZZZ = "Z"\n',
        "other/ARC001-one.md": support.rule("ARC001", "one"),
        "other/ZZZ001-loud.md": support.rule("ZZZ001", "loud", "# Loud\n"),
    }
    for name, data in files.items():
        wio.put(f"{support.RULES}/{name}", data)
    support.work(wio, support.WORK, 'roots = ["api"]\n')


def _outputs(wio: Wio) -> list[str]:
    """Run the commands of AC-3 and collect what they print.

    Args:
        wio: The facade.

    Returns:
        The text and the JSON of `list` and of `check`, and the text of `show`.
    """
    flags: list[list[str]] = [[], ["--json"]]
    out = [wio.run(["rules", "list", *_VIEW, *more]).stdout for more in flags]
    out += [wio.run(["rules", "check", *more]).stdout for more in flags]
    out.append(wio.run(["rules", "show", "demo.ARC001"]).stdout)
    return out


@_BOTH
def test_the_same_inputs_give_the_same_bytes_in_the_order_of_the_rules(
    wio: Wio,
) -> None:
    """AC-3: whatever the order of the tables and the rule presets of the config."""
    # Given rules of two rulesets and a config that is rewritten in the other order
    _ordered_repo(wio)
    first = _outputs(wio)

    # When the config lists its tables and rule presets in the opposite order and the
    # commands run again
    wio.put(".agents/wio/config.toml", _order_config(reverse=True))
    second = _outputs(wio)

    # Then every output is byte for byte the same; `list` orders the rules by
    # ruleset, family and number, `check` its warning before its error, and the JSON
    # holds what the text holds
    assert first == second
    listed, listed_json, checked, checked_json, shows = first
    codes = [
        "demo.ARC001",
        "demo.ARC002",
        "demo.PAY001",
        "other.ARC001",
        "other.ZZZ001",
    ]
    assert re.findall(r"^(\w+\.[A-Z]+\d+) ", listed, re.MULTILINE) == codes
    assert [r["code"] for r in json.loads(listed_json)["rules"]] == codes
    assert checked.index("ZZZ001") < checked.index("demo.XYZ")
    assert len(json.loads(checked_json)) == len(checked.strip().splitlines())
    assert shows.startswith("demo.ARC001  one\n")
