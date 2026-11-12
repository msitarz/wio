# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio contracts check`, which reports every problem of the Works."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

WORKS = ".agents/wio/works"
PASSES = "The contracts pass.\n"
KEY_HINT = "Unknown key `depend_on` in the metadata. Did you mean `depends_on`?"
CYCLE = (
    "Dependency cycle: cyc001 → cyc002 (listed in depends_on) → cyc001 "
    "(listed in depends_on)"
)
PROBLEMS = [
    ("error", f"{WORKS}/c1/README.md", CYCLE),
    ("warning", f"{WORKS}/k/README.md", KEY_HINT),
    ("error", f"{WORKS}/t/README.md", "The template `nosuch` does not exist"),
    (
        "error",
        f"{WORKS}/s1/README.md, {WORKS}/s2/README.md",
        "Works share the id `dup001`",
    ),
]
REJECTED = (
    "The template `{}` is rejected by `wio templates check`; run it for the findings"
)


def _lines(rows: list[tuple[str, str, str]]) -> str:
    """Write the lines that `check` prints for some findings.

    Args:
        rows: The severity, the place and the message of each.

    Returns:
        The text, one `<severity>: <place>: <message>` line each.
    """
    return "".join(f"{s}: {where}: {message}\n" for s, where, message in rows)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_every_problem_at_once_and_exits_by_severity(wio: Wio) -> None:
    """AC-1: a shared id, a cycle, a key and a template, in one fixed order."""
    # Given a project whose defaults have `deliver`, with a shared id, a cycle, an
    # unknown key and a missing template
    wio.fixture("contracts/check-problems")

    # When `wio contracts check` runs, and then with `--json`
    text = wio.run(["contracts", "check"])
    as_json = wio.run(["contracts", "check", "--json"])

    # Then both report the four, the second as one array that parses, and each
    # exits 1
    assert text.stdout == _lines(PROBLEMS)
    assert [
        (d["severity"], d["where"], d["message"]) for d in json.loads(as_json.stdout)
    ] == PROBLEMS
    assert as_json.stdout == json.dumps(json.loads(as_json.stdout)) + "\n"
    assert (text.stderr, text.exit_code) == ("", 1)
    assert (as_json.stderr, as_json.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_clean_tree_passes(wio: Wio) -> None:
    """AC-1: nothing to report is one sentence and exit 0."""
    # Given a tree with no problem
    wio.fixture("contracts/check-clean")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then it says that the contracts pass and exits 0
    assert (output.stdout, output.stderr, output.exit_code) == (PASSES, "", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_warning_does_not_fail_the_check(wio: Wio) -> None:
    """AC-1: a tree whose only problem is a warning exits 0."""
    # Given a tree whose only problem is an unknown key
    wio.fixture("contracts/check-warning")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then it prints the warning and exits 0
    assert output.stdout == _lines([("warning", f"{WORKS}/a/README.md", KEY_HINT)])
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_mistyped_key_is_told_by_its_closest_known_key(wio: Wio) -> None:
    """AC-2: an unknown key or table is a warning, `[x]` and `tracks` are not."""
    # Given Works with `depend_on`, `zzz`, a plain `x` and the table `[xx]`, and
    # Works with the table `[x]` and the key `tracks`
    wio.fixture("contracts/check-keys")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then the first four are warned of at their files, with a suggestion only for
    # the first, and the second group gives nothing
    assert output.stdout == _lines(
        [
            ("warning", f"{WORKS}/a/README.md", KEY_HINT),
            ("warning", f"{WORKS}/b/README.md", "Unknown key `zzz` in the metadata"),
            ("warning", f"{WORKS}/c/README.md", "Unknown key `x` in the metadata"),
            ("warning", f"{WORKS}/d/README.md", "Unknown key `xx` in the metadata"),
        ]
    )
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_an_id_that_would_break_a_record_is_an_error(wio: Wio) -> None:
    """AC-3: whitespace, a comma and `none` are refused, other ids are not."""
    # Given five Works with the ids `a b`, `a,b`, `none`, `SPEC-012` and `k3m9xq`
    wio.fixture("contracts/check-ids")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then the first three are errors and the last two give nothing
    assert output.stdout == _lines(
        [
            (
                "error",
                f"{WORKS}/a/README.md",
                "The id `a b` holds whitespace or a comma",
            ),
            (
                "error",
                f"{WORKS}/b/README.md",
                "The id `a,b` holds whitespace or a comma",
            ),
            (
                "error",
                f"{WORKS}/c/README.md",
                "The id `none` is reserved for commits that belong to no Work",
            ),
        ]
    )
    assert (output.stderr, output.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_missing_and_a_rejected_template_are_told_apart(wio: Wio) -> None:
    """AC-4: each is an error naming the template, with no action error."""
    # Given Works that name `nosuch`, `bad` and `unclosed`, and one that names
    # none
    wio.fixture("contracts/check-templates")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then the first is missing, the next two are rejected, and the last gives nothing
    assert output.stdout == _lines(
        [
            (
                "error",
                f"{WORKS}/a/README.md",
                "The template `nosuch` does not exist",
            ),
            ("error", f"{WORKS}/b/README.md", REJECTED.format("bad")),
            ("error", f"{WORKS}/c/README.md", REJECTED.format("unclosed")),
        ]
    )
    assert (output.stderr, output.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_actions_a_work_names_exist(wio: Wio) -> None:
    """AC-5: an undeclared action, preset and stage, and a repeat, are errors."""
    # Given the config of the contract and Works whose `[actions]` hold its faults,
    # and one whose empty list leaves `amend`
    wio.fixture("contracts/check-actions")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then the first four are errors in the words of the contract, and the empty
    # list is told nothing
    assert output.stdout == _lines(
        [
            (
                "error",
                f"{WORKS}/a/README.md",
                "The action `shipp` is not declared in `[actions]` of the config",
            ),
            (
                "error",
                f"{WORKS}/b/README.md",
                "The stage preset `nosuch` of action `deliver` is not declared",
            ),
            (
                "error",
                f"{WORKS}/c/README.md",
                "The stage `implementation` appears twice in action `deliver`",
            ),
            (
                "error",
                f"{WORKS}/d/README.md",
                "The stage `gone` of action `deliver` is not declared",
            ),
        ]
    )
    assert (output.stderr, output.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_repeat_that_a_work_inherits_is_reported_at_its_own_file(wio: Wio) -> None:
    """AC-5: no other command judges a pipeline that a template gives."""
    # Given a template whose action repeats a stage and a Work that follows it
    wio.fixture("contracts/check-inherited-repeat")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then the repeat is an error at the Work's file
    assert output.stdout == _lines(
        [
            (
                "error",
                f"{WORKS}/a/README.md",
                "The stage `implementation` appears twice in action `deliver`",
            )
        ]
    )
    assert (output.stderr, output.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("fixture", "passes"),
    [
        ("contracts/check-no-defaults", False),
        ("contracts/check-removed", False),
        ("contracts/check-defaults", True),
    ],
)
def test_a_work_that_resolves_to_no_action_is_an_error(
    wio: Wio, fixture: str, *, passes: bool
) -> None:
    """AC-5: no default or a removed action leaves none; the defaults give one."""
    # Given a project with no defaults, one whose Work removes the only action of
    # its template, or one with defaults
    wio.fixture(fixture)

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then the first two give the error and the third nothing
    expected = (
        PASSES
        if passes
        else _lines(
            [("error", f"{WORKS}/a/README.md", "The Work resolves to no action")]
        )
    )
    assert output.stdout == expected
    assert (output.stderr, output.exit_code) == ("", 0 if passes else 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_roots_a_work_names_exist(wio: Wio) -> None:
    """AC-6: an undeclared root, `@descendants` in a leaf and omitted roots."""
    # Given a nesting project with an undeclared root, a leaf that lists
    # `@descendants`, and a parent that leaves out roots of its children
    wio.fixture("contracts/check-roots")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then the error, the warning and the two notes are reported, and it exits 1
    assert output.stdout == _lines(
        [
            (
                "error",
                f"{WORKS}/a/README.md",
                "The root `nosuch` is not declared in `[roots]` of the config",
            ),
            (
                "warning",
                f"{WORKS}/b/README.md",
                "The Work has no children, so `@descendants` adds no root",
            ),
            (
                "note",
                f"{WORKS}/c/README.md",
                "Its roots leave out `api`, which a descendant uses",
            ),
            (
                "note",
                f"{WORKS}/c/README.md",
                "Its roots leave out `db`, which a descendant uses",
            ),
        ]
    )
    assert (output.stderr, output.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_several_problems_of_one_work_are_all_reported_once(wio: Wio) -> None:
    """AC-7: every concern for every Work, and a skip for what discovery reported."""
    # Given a Work with an unknown key, an undeclared root and an undeclared action,
    # a parent whose `roots` is a string, and a Work whose `template` is a number
    wio.fixture("contracts/check-several")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then the first gets a warning and two errors, the parent only the error of
    # discovery and no note, and the last only the error of discovery
    assert output.stdout == _lines(
        [
            (
                "error",
                f"{WORKS}/a/README.md",
                "The action `shipp` is not declared in `[actions]` of the config",
            ),
            (
                "error",
                f"{WORKS}/a/README.md",
                "The root `nosuch` is not declared in `[roots]` of the config",
            ),
            (
                "warning",
                f"{WORKS}/a/README.md",
                "Unknown key `bogus_key` in the metadata",
            ),
            ("error", f"{WORKS}/c/README.md", "`roots` must be an array of strings"),
            ("error", f"{WORKS}/t/README.md", "`template` must be a string"),
        ]
    )
    assert (output.stderr, output.exit_code) == ("", 1)
