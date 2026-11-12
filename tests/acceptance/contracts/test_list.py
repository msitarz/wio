# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio contracts list`, which shows the Works of a project."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.results import Output
    from tests.acceptance.dsl.wio import Wio

WORKS = ".agents/wio/works"
HINT = "`wio contracts check` shows every problem."
NESTING_TEXT = f"""\
p5n2hv  Parent  [feature.parent]
        {WORKS}/p/README.md
        roots: @descendants
  k3m9xq  Child one  [feature.leaf]
          {WORKS}/p/a/README.md
          roots: wio, api
          actions: deliver = [build, run], define = define-feature, amend = none
  a7b2c4  Child two
          {WORKS}/p/b/README.md
          after: k3m9xq Child one
          after: n5p7qr (no title)
          after: y4k2mq (not found)
  n5p7qr  (no title)
          {WORKS}/p/c/README.md
"""
FLAT_TEXT = f"""\
k3m9xq    Alpha  [feature.leaf]
          {WORKS}/a/README.md
spec0012  Beta
          {WORKS}/b/README.md
          roots: api
n5p7qr    (no title)
          {WORKS}/c/README.md
"""


def _work(
    work_id: str,
    path: str,
    title: str | None,
    parent: str | None,
    template: str | None = None,
    roots: list[str] | None = None,
    depends_on: list[str] | None = None,
    actions: dict[str, object] | None = None,
) -> dict[str, object]:
    """Write the JSON object that `list` gives for a Work.

    Args:
        work_id: The id.
        path: The file, relative to the Works directory.
        title: The title, or `None`.
        parent: The id of the parent, or `None`.
        template: The template, or `None`.
        roots: The roots as written.
        depends_on: The dependencies as written.
        actions: The `[actions]` overrides.

    Returns:
        The object, with its fields in the order of the contract.
    """
    return {
        "id": work_id,
        "title": title,
        "path": f"{WORKS}/{path}",
        "template": template,
        "roots": roots or [],
        "depends_on": depends_on or [],
        "actions": actions or {},
        "parent": parent,
    }


NESTING_JSON = [
    _work("p5n2hv", "p/README.md", "Parent", None, "feature.parent", ["@descendants"]),
    _work(
        "k3m9xq",
        "p/a/README.md",
        "Child one",
        "p5n2hv",
        "feature.leaf",
        ["wio", "api"],
        actions={
            "deliver": ["build", "run"],
            "define": "define-feature",
            "amend": [],
        },
    ),
    _work(
        "a7b2c4",
        "p/b/README.md",
        "Child two",
        "p5n2hv",
        depends_on=["k3m9xq", "n5p7qr", "y4k2mq"],
    ),
    _work("n5p7qr", "p/c/README.md", None, "p5n2hv"),
]
FLAT_JSON = [
    _work("k3m9xq", "a/README.md", "Alpha", None, "feature.leaf"),
    _work("spec0012", "b/README.md", "Beta", None, roots=["api"]),
    _work("n5p7qr", "c/README.md", None, None),
]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_works_are_listed_with_their_hierarchy_and_their_overrides(
    wio: Wio,
) -> None:
    """AC-1: each Work is a block, its children are indented, overrides show."""
    # Given a nesting project with a parent and three children
    wio.fixture("contracts/list-nesting")

    # When `wio contracts list` runs
    output = wio.run(["contracts", "list"])

    # Then it prints the blocks of the contract and exits 0
    assert output.stdout == NESTING_TEXT
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_under_flat_every_work_is_at_the_same_indent(wio: Wio) -> None:
    """AC-2: there is no nesting, and the id column is as wide as the widest id."""
    # Given a flat project with three Works
    wio.fixture("contracts/list-flat")

    # When `wio contracts list` runs
    output = wio.run(["contracts", "list"])

    # Then the blocks are at one indent in the order of the paths, and it exits 0
    assert output.stdout == FLAT_TEXT
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_json_is_one_array_with_the_same_facts(wio: Wio) -> None:
    """AC-3: one array on one line, in the order of the paths."""
    # Given the nesting project
    wio.fixture("contracts/list-nesting")

    # When `wio contracts list --json` runs
    output = wio.run(["contracts", "list", "--json"])

    # Then it is one line that `json.dumps` writes, with the objects of the
    # contract in the order of the paths, and it exits 0
    array = json.loads(output.stdout)
    assert output.stdout == json.dumps(array) + "\n"
    assert array == NESTING_JSON
    assert [list(obj) for obj in array] == [list(obj) for obj in NESTING_JSON]
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_json_has_no_parent_and_nulls_under_flat(wio: Wio) -> None:
    """AC-3: under `flat` every parent is null, and a missing heading is null."""
    # Given the flat project
    wio.fixture("contracts/list-flat")

    # When `wio contracts list --json` runs
    output = wio.run(["contracts", "list", "--json"])

    # Then it is one line with the objects of the contract and no parent
    array = json.loads(output.stdout)
    assert output.stdout == json.dumps(array) + "\n"
    assert array == FLAT_JSON
    assert (output.stderr, output.exit_code) == ("", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_tree_with_no_work_prints_nothing(wio: Wio) -> None:
    """AC-4: an empty tree is not an error."""
    # Given a repository with no Work
    wio.fixture("contracts/list-empty")

    # When `list` and `list --json` run
    text = wio.run(["contracts", "list"])
    array = wio.run(["contracts", "list", "--json"])

    # Then the first prints nothing, the second `[]`, and each exits 0
    assert (text.stdout, text.stderr, text.exit_code) == ("", "", 0)
    assert (array.stdout, array.stderr, array.exit_code) == ("[]\n", "", 0)


def _refused(wio: Wio) -> list[Output]:
    """Run `list` in both forms on the repository of the scenario.

    Args:
        wio: The facade.

    Returns:
        The output of the text form and of the JSON form.
    """
    return [
        wio.run(["contracts", "list"]),
        wio.run(["contracts", "list", "--json"]),
    ]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_shared_id_refuses_the_listing(wio: Wio) -> None:
    """AC-5: two Works with one id list nothing in either form."""
    # Given a tree with two Works with one id
    wio.fixture("contracts/list-shared-id")

    # When `list` and `list --json` run
    outputs = _refused(wio)

    # Then each writes nothing to standard output, names both paths and ends with
    # the hint on standard error, and exits 2
    for output in outputs:
        assert output.stdout == ""
        assert output.exit_code == 2
        assert f"{WORKS}/s/README.md" in output.stderr
        assert f"{WORKS}/t/README.md" in output.stderr
        assert output.stderr.rstrip().endswith(HINT)
        assert output.stderr.startswith("error: ")
        assert "error: error:" not in output.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_an_unreadable_work_file_refuses_the_listing(wio: Wio) -> None:
    """AC-5: a Work file that cannot be read lists nothing in either form."""
    # Given a tree with a Work file that is not UTF-8
    wio.fixture("contracts/list-unreadable")
    wio.put(f"{WORKS}/b/README.md", b"\xff\xfe not text")

    # When `list` and `list --json` run
    outputs = _refused(wio)

    # Then each writes nothing to standard output, names the file and ends with
    # the hint on standard error, and exits 2
    for output in outputs:
        assert output.stdout == ""
        assert output.exit_code == 2
        assert f"{WORKS}/b/README.md" in output.stderr
        assert output.stderr.rstrip().endswith(HINT)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_errors_that_do_not_leave_the_tree_incomplete_do_not_refuse(
    wio: Wio,
) -> None:
    """AC-5: an undeclared root, a wrong type and a cycle still list."""
    # Given a Work with a root that is not declared, one whose `roots` is a
    # string, and two Works that list each other
    wio.fixture("contracts/list-soft-errors")

    # When `wio contracts list` runs
    output = wio.run(["contracts", "list"])

    # Then all four are listed and the exit code is 0
    assert output.exit_code == 0
    for work_id in ("k3m9xq", "n5p7qr", "a7b2c4", "y4k2mq"):
        assert f"{work_id}  " in output.stdout
    assert "roots: nosuch" in output.stdout
    assert "after: y4k2mq Waits for the last" in output.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_listing_writes_nothing_and_prints_the_same_bytes_twice(wio: Wio) -> None:
    """AC-6: two runs print the same, and no contract changes."""
    # Given the Works of AC-1 and a fingerprint of each contract
    wio.fixture("contracts/list-nesting")
    before = wio.fingerprint(WORKS)

    # When `list` and `list --json` each run twice
    texts = [wio.run(["contracts", "list"]) for _ in range(2)]
    arrays = [wio.run(["contracts", "list", "--json"]) for _ in range(2)]

    # Then the two outputs of each are identical, and every contract is the same
    assert texts[0].stdout == texts[1].stdout != ""
    assert arrays[0].stdout == arrays[1].stdout != ""
    assert wio.fingerprint(WORKS) == before
    assert len(before) == 4
