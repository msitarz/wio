# SPDX-License-Identifier: Apache-2.0
"""Scenarios of the body checks of `wio contracts check`."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

A = ".agents/wio/works/a/README.md"
B = ".agents/wio/works/b/README.md"
PASSES = "The contracts pass.\n"
MISSING_GOALS = f"error: {A}: The section `Goals` is required by the template `t`\n"
KEY = (
    f"warning: {B}: Unknown key `depend_on` in the metadata. "
    "Did you mean `depends_on`?\n"
)
IGNORED = "The directive list is ignored because the contract follows the template `t`"
LEVEL_TWO = "Directives are read on level-2 headings only"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_required_section_that_is_missing_is_an_error(wio: Wio) -> None:
    """AC-1: one error at the file, and a section matches in another case."""
    # Given a template that requires `Purpose` and `Goals` and has `Notes`, and a
    # contract with `##  purpose` only
    wio.fixture("contracts/check-body-required")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then there is one error for `Goals`, and none for `Purpose` or `Notes`
    assert output.stdout == MISSING_GOALS
    assert (output.stderr, output.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_body_is_reported_in_the_same_run_as_the_metadata(wio: Wio) -> None:
    """AC-1: the missing section and the unknown key, in one order."""
    # Given the same project and another Work with the unknown key `depend_on`
    wio.fixture("contracts/check-body-required-key")

    # When `wio contracts check` runs, and with `--json`
    text = wio.run(["contracts", "check"])
    as_json = wio.run(["contracts", "check", "--json"])

    # Then both report the missing section and the key in the same order, the
    # second as one array that parses, and each exits 1
    assert text.stdout == MISSING_GOALS + KEY
    assert [(d["severity"], d["where"]) for d in json.loads(as_json.stdout)] == [
        ("error", A),
        ("warning", B),
    ]
    assert (text.exit_code, as_json.exit_code) == (1, 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_items_and_their_ids_are_judged_as_the_items_leaf_judges_them(wio: Wio) -> None:
    """AC-2: the count and the ids come from the template."""
    # Given a template with `items>=1` and a `pattern`, and a contract whose Goals
    # holds only an authoring comment and whose criteria repeat an id and lack one
    wio.fixture("contracts/check-body-items")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then there are one error at `## Goals`, one at the first `AC-1` naming the
    # line of the second, and one at `### Third`
    assert [line.split(": ")[1] for line in output.lines] == [
        f"{A}:8",
        f"{A}:14",
        f"{A}:18",
    ]
    assert "asks for 1 item, and the section holds 0 items" in output.lines[0]
    assert "used again on line 16" in output.lines[1]
    assert "the item has no id" in output.lines[2]
    assert (output.stderr, output.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_misspelled_section_is_a_warning_with_a_suggestion(wio: Wio) -> None:
    """AC-3: a stray `##` heading is told, and a deeper heading is free."""
    # Given a template with `Constraints` and a contract with `Constraint`, `Zzz`
    # and a deeper heading
    wio.fixture("contracts/check-body-sections")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then there are two warnings at their lines, the first with the suggestion,
    # and the command exits 0
    assert output.stdout == (
        f"warning: {A}:8: The section `Constraint` is not in the template `t`. "
        "Did you mean `Constraints`?\n"
        f"warning: {A}:14: The section `Zzz` is not in the template `t`\n"
    )
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_contract_without_a_template_gets_no_section_warning(wio: Wio) -> None:
    """AC-3: sections of its own are free."""
    # Given a contract that names no template and has sections of its own
    wio.fixture("contracts/check-body-no-template")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then there is no warning about a section
    assert (output.stdout, output.stderr, output.exit_code) == (PASSES, "", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_directive_list_in_a_contract_that_follows_a_template_is_ignored(
    wio: Wio,
) -> None:
    """AC-4: such a list is a warning and changes nothing."""
    # Given a template that requires `Goals`, and a contract that lacks it and has
    # lists on `Notes`, `Bad` and a deeper heading
    wio.fixture("contracts/check-body-ignored")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then there is one warning for each list, no parser error and no stray
    # section, and the error for the missing `Goals`
    assert output.stdout == (
        MISSING_GOALS
        + f"warning: {A}:8: {IGNORED}\n"
        + f"warning: {A}:12: {IGNORED}\n"
        + f"warning: {A}:16: {IGNORED}\n"
    )
    assert (output.stderr, output.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_contract_without_a_template_is_checked_by_its_own_headings(
    wio: Wio,
) -> None:
    """AC-5: its lists are read, and a list that cannot be read is an error."""
    # Given a contract with no template whose headings carry directives, one of
    # them wrong and one on a deeper heading
    wio.fixture("contracts/check-body-own")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then there are the error for the items, the parser's error at its line and
    # column, and the error for the deeper heading at its opener, and none for
    # `Purpose`
    assert [line.split(": ")[1] for line in output.lines] == [
        f"{A}:11",
        f"{A}:15:18",
        f"{A}:19:10",
    ]
    assert "asks for 2 items, and the section holds 1 item" in output.lines[0]
    assert "Unknown directive `mandatory`" in output.lines[1]
    assert output.lines[2].endswith(LEVEL_TWO)
    assert (output.stderr, output.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_contract_with_no_directives_has_no_body_diagnostic(wio: Wio) -> None:
    """AC-5: nothing to read, nothing to report."""
    # Given a contract with no template and no directive list
    wio.fixture("contracts/check-body-plain")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then the contracts pass
    assert (output.stdout, output.stderr, output.exit_code) == (PASSES, "", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_repeated_section_and_a_missing_title_are_warnings(wio: Wio) -> None:
    """AC-6: a repeat carries nothing, and a contract with no heading is told."""
    # Given a contract with `Goals` twice under a template that wants two items,
    # and a second contract with no heading
    wio.fixture("contracts/check-body-repeats")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then the first's items are too few, the repeat is a warning, and the second
    # contract has no title
    assert [
        line.split(": ", 1)[0] + " " + line.split(": ")[1] for line in output.lines
    ] == [
        f"error {A}:8",
        f"warning {A}:12",
        f"warning {B}",
    ]
    assert "The section `Goals` is repeated; the first one counts" in output.lines[1]
    assert output.lines[2].endswith("The contract has no title")
    assert (output.stderr, output.exit_code) == ("", 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_fresh_work_that_requires_only_headings_passes(wio: Wio) -> None:
    """AC-8: what an entry template requires decides what a Work needs."""
    # Given a template that requires `Purpose` and a contract made from it with
    # its Purpose written
    wio.fixture("contracts/check-body-fresh-headings")

    # When `wio contracts check` runs
    output = wio.run(["contracts", "check"])

    # Then it passes
    assert (output.stdout, output.stderr, output.exit_code) == (PASSES, "", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_fresh_work_that_requires_an_item_fails_until_it_has_one(wio: Wio) -> None:
    """AC-8: an authoring comment is no item, and a written item is."""
    # Given a template that requires `items>=1` on Goals and a contract made from
    # it whose Goals holds only the authoring comment
    wio.fixture("contracts/check-body-fresh-items")

    # When `wio contracts check` runs, then a first item is written under Goals
    # and it runs again
    before = wio.run(["contracts", "check"])
    wio.put(
        A,
        b'<!-- wio\nid = "bod001"\ntemplate = "t"\n-->\n\n# Title\n\n## Goals\n\n'
        b"<!-- Write the goals. -->\n\n- First goal\n",
    )
    after = wio.run(["contracts", "check"])

    # Then the first run has one error at `## Goals`, and the second passes
    assert [line.split(": ")[1] for line in before.lines] == [f"{A}:8"]
    assert before.exit_code == 1
    assert (after.stdout, after.stderr, after.exit_code) == (PASSES, "", 0)
