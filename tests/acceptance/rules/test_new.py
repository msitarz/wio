# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio rules new`, which creates the next rule of a family."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.rules.support import BASE, RULES, rule, ruleset

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

NOT_DONE = pytest.mark.xfail(strict=True, reason="wio rules new is a stub")
CONFIG = (
    '[roots.api]\npaths = ["src"]\nrule_presets = ["demo.recommended"]\n'
    '[rulesets.demo]\nalias = "d"\n'
    '[stages.s]\ngoal = "g"\nrules_include = ["demo.ARC"]\n'
)
MANIFEST = (
    '[families]\nARC = "A"\nPAY = "P"\n'
    '[rule_presets.recommended]\nrules_include = ["ARC"]\n'
)
NEW = f"{RULES}/demo/ARC004-keep-it-small.md"


def _repo(wio: Wio, *, front_matter: bool = False) -> None:
    """Start the repository: `demo` with `ARC001` to `ARC003` and an alias `d`.

    Args:
        wio: The facade.
        front_matter: Whether its rules are written with `+++` front matter.
    """
    wio.fixture(BASE)
    wio.put(".agents/wio/config.toml", CONFIG.encode())
    ruleset(wio, "demo", MANIFEST, {"ARC001": "a", "ARC002": "b", "ARC003": "c"})
    if front_matter:
        for number in (1, 2, 3):
            text = f'+++\nwio = 1\ncode = "ARC00{number}"\nname = "r{number}"\n+++\n'
            wio.put(f"{RULES}/demo/ARC00{number}-r{number}.md", text.encode())


@NOT_DONE
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_new_rule_gets_the_next_code_and_the_result_says_what_selects_it(
    wio: Wio,
) -> None:
    """AC-1, AC-9: `ARC004`, its file, and the two origins."""
    # Given the repository, where a rule preset and a stage select `ARC`
    _repo(wio)

    # When `wio rules new demo ARC --name keep-it-small` runs
    output = wio.run(["rules", "new", "demo", "ARC", "--name", "keep-it-small"])

    # Then it creates `ARC004` and says what selects it
    assert output.exit_code == 0
    assert output.stdout.splitlines() == [
        "created demo.ARC004 keep-it-small",
        f"file: {NEW}",
        "selected: demo.ARC004 ← root api ← demo.recommended ← demo.ARC",
        "selected: demo.ARC004 ← stage s ← demo.ARC",
    ]


@NOT_DONE
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_family_that_nothing_includes_is_not_selected_yet(wio: Wio) -> None:
    """AC-9: the third line says that nothing selects the new rule."""
    # Given the repository, where no entry includes `PAY`
    _repo(wio)

    # When `wio rules new demo PAY --name pay-later` runs
    output = wio.run(["rules", "new", "demo", "PAY", "--name", "pay-later"])

    # Then it creates `PAY001` and says that nothing selects it yet
    assert output.stdout.splitlines()[:3] == [
        "created demo.PAY001 pay-later",
        f"file: {RULES}/demo/PAY001-pay-later.md",
        "selected: no, nothing selects it yet",
    ]


@NOT_DONE
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_json_is_one_line_with_a_fixed_order(wio: Wio) -> None:
    """AC-10: the fields in order, and the chains of labels as arrays."""
    # Given the repository
    _repo(wio)

    # When `wio rules new demo ARC --name keep-it-small --json` runs
    output = wio.run(
        ["rules", "new", "demo", "ARC", "--name", "keep-it-small", "--json"]
    )

    # Then the document is one line with `code` qualified and the two chains
    assert output.stdout.count("\n") == 1
    found = json.loads(output.stdout)
    assert list(found) == ["code", "name", "path", "selected", "origins"]
    assert (found["code"], found["selected"], found["path"]) == (
        "demo.ARC004",
        True,
        NEW,
    )
    assert found["origins"] == [
        ["root api", "demo.recommended", "demo.ARC"],
        ["stage s", "demo.ARC"],
    ]


@NOT_DONE
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_file_is_in_the_comment_form_whatever_form_the_others_have(
    wio: Wio,
) -> None:
    """AC-4: the block starts the file, the others are unchanged, `list` reads it."""
    # Given a ruleset whose rules use `+++` front matter
    _repo(wio, front_matter=True)
    before = wio.fingerprint(f"{RULES}/demo")

    # When a rule is created with a description that has special characters
    text = 'Use "quotes", a \\ and --> carefully.'
    output = wio.run(
        [
            "rules",
            "new",
            "demo",
            "ARC",
            "--name",
            "keep-it-small",
            "--description",
            text,
        ]
    )

    # Then the file is a comment block with an empty body, the others are
    # unchanged, and the rule reads back with exactly that description
    assert output.exit_code == 0
    assert wio.read(NEW).startswith(b"<!-- wio\n")
    after = wio.fingerprint(f"{RULES}/demo")
    assert {k: v for k, v in after.items() if k in before} == before
    listed = json.loads(wio.run(["rules", "list", "demo.ARC004", "--json"]).stdout)
    assert listed["rules"][0]["description"] == text


@NOT_DONE
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_an_alias_is_accepted_and_the_canonical_name_is_shown(wio: Wio) -> None:
    """AC-5: `d` works, and the result says `demo`."""
    # Given the repository, where `d` is the alias of `demo`
    _repo(wio)

    # When the rule is created for `d`
    output = wio.run(["rules", "new", "d", "ARC", "--name", "keep-it-small"])

    # Then the file is in `demo` and the result says `demo.ARC004`
    assert output.stdout.startswith("created demo.ARC004 ")
    assert "d.ARC" not in output.stdout.replace("demo.ARC", "")
    assert wio.read(NEW)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("args", "message"),
    [
        pytest.param(["nope", "ARC", "--name", "x"], "demo", marks=NOT_DONE),
        pytest.param(["demo", "ZZZ", "--name", "x"], "ARC", marks=NOT_DONE),
        pytest.param(
            ["demo", "ARC", "--name", "Bad_Name"], "lower-case", marks=NOT_DONE
        ),
        pytest.param(
            ["demo", "ARC", "--name", "x", "--description", ""],
            "one line",
            marks=NOT_DONE,
        ),
        pytest.param(["demo", "ARC", "--name", "a"], "demo.ARC001", marks=NOT_DONE),
        pytest.param(
            ["demo", "ARC", "--name", "other"], "ARC004-other.md", marks=NOT_DONE
        ),
    ],
    ids=["ruleset", "family", "name", "description", "taken", "exists"],
)
def test_a_request_that_cannot_be_met_is_refused_and_writes_nothing(
    wio: Wio, args: list[str], message: str
) -> None:
    """AC-6: exit 2, the cause on standard error, and no file written."""
    # Given the repository and an unmarked file that the next code would use
    _repo(wio)
    wio.put(f"{RULES}/demo/ARC004-other.md", b"Not a rule.\n")
    before = wio.fingerprint(RULES)

    # When the request runs
    output = wio.run(["rules", "new", *args])

    # Then it exits 2, names the cause, prints nothing and changes nothing
    assert output.exit_code == 2
    assert message in output.stderr
    assert not output.stdout
    assert wio.fingerprint(RULES) == before


@NOT_DONE
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_fault_in_another_ruleset_refuses_and_a_warning_does_not(wio: Wio) -> None:
    """AC-7, AC-8: an error anywhere refuses, a warning refuses nothing."""
    # Given a ruleset `bad` with a block that does not close
    _repo(wio)
    ruleset(wio, "bad", "", {})
    wio.put(f"{RULES}/bad/ARC001-open.md", b"<!-- wio\n")
    before = wio.fingerprint(RULES)

    # When a rule is created, and again once the fault is a warning
    refused = wio.run(["rules", "new", "demo", "ARC", "--name", "keep-it-small"])
    refused_state = wio.fingerprint(RULES)
    wio.put(
        f"{RULES}/bad/ARC001-open.md", rule("ARC001", "open", extra='owner = "x"\n')
    )
    allowed = wio.run(["rules", "new", "demo", "ARC", "--name", "keep-it-small"])

    # Then the first exits 2 and writes nothing, and the second creates the rule
    assert (refused.exit_code, refused.stdout) == (2, "")
    assert "ARC001-open.md" in refused.stderr
    assert refused_state == before
    assert allowed.exit_code == 0
