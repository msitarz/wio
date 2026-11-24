# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio rules list` as a whole: a view, references and `--explain`."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.rules.support import (
    BASE,
    RULES,
    WORK,
    header,
    rule,
    ruleset,
    shown,
    work,
)

if TYPE_CHECKING:
    from tests.acceptance.dsl.results import Output
    from tests.acceptance.dsl.wio import Wio

_RECOMMENDED = "root api ← demo.recommended ← demo.ARC"


def _repo(wio: Wio, *, web: bool = False, bad: bool = False) -> None:
    """Start the repository of AC-1, and with `web` or `bad` those of AC-2 and AC-3.

    Args:
        wio: The facade.
        web: Whether to add the ruleset `web`, whose rule no root reaches.
        bad: Whether to add the ruleset `bad`, which holds two rules of one code.
    """
    wio.fixture(BASE)
    config = (
        '[roots.api]\npaths = ["src/api"]\nrule_presets = ["demo.recommended"]\n'
        '[stages.s]\ngoal = "g"\nrules_include = ["demo.PAY001"]\n'
    )
    wio.put(".agents/wio/config.toml", config.encode())
    manifest = '[families]\nARC = "A"\nPAY = "P"\n'
    manifest += '[rule_presets.recommended]\nrules_include = ["ARC"]\n'
    manifest += 'rules_exclude = ["ARC002"]\n'
    ruleset(
        wio, "demo", manifest, {"ARC001": "keep", "ARC002": "name", "PAY002": "late"}
    )
    wio.put(
        f"{RULES}/demo/PAY001-pay.md",
        rule("PAY001", "pay", extra='description = "Pay first."\n').replace(
            b"Body.", b"Pay."
        ),
    )
    work(wio, WORK, 'roots = ["api"]\n')
    if web:
        ruleset(wio, "web", '[families]\nWEB = "W"\n', {"WEB001": "page"})
    if bad:
        ruleset(wio, "bad", '[families]\nBAD = "B"\n', {"BAD001": "one"})
        wio.put(f"{RULES}/bad/BAD001-two.md", rule("BAD001", "two"))


def _blocks(output: Output) -> dict[str, list[str]]:
    """Read the blocks of the text.

    Args:
        output: The result of `wio rules list`.

    Returns:
        The detail lines of each qualified code, stripped, in the order printed.
    """
    found: dict[str, list[str]] = {}
    for line in output.stdout.split("\n\n", 1)[-1].splitlines():
        if line and not line[0].isspace():
            found[line.split()[0]] = []
        elif line:
            found[list(found)[-1]].append(line.strip())
    return found


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_one_command_serves_a_view_references_and_an_explanation(wio: Wio) -> None:
    """AC-1: the Work at a stage, narrowed by `demo.all` and explained."""
    # Given the repository and a Work in `api`
    _repo(wio)

    # When the command runs with `demo.all` and `--explain`, and with `demo.ARC`
    explained = wio.run(
        ["rules", "list", "demo.all", "--work", WORK, "--stage", "s", "--explain"]
    )
    narrowed = wio.run(["rules", "list", "demo.ARC", "--work", WORK, "--stage", "s"])

    # Then the first shows every rule of `demo` with its origin or its reason,
    # under a header that names the layers, and the second only `ARC001` with no
    # explanation line
    assert header(explained) == [
        f"view: Work {WORK}",
        "layers: roots, stage, always fields",
        "roots: api",
        "stage: s",
        "references: demo.all",
    ]
    blocks = _blocks(explained)
    assert f"from: demo.ARC001 ← {_RECOMMENDED}" in blocks["demo.ARC001"]
    assert "Pay first." in blocks["demo.PAY001"]
    assert "from: demo.PAY001 ← stage s ← demo.PAY001" in blocks["demo.PAY001"]
    assert "out: excluded by the root's rule preset" in blocks["demo.ARC002"]
    assert "out: not selected" in blocks["demo.PAY002"]
    assert list(shown(narrowed)) == ["demo.ARC001"]
    assert not any(tag in narrowed.stdout for tag in ("from:", "out:", "by:"))


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("args", "codes"),
    [
        ([], ["demo.ARC002", "demo.PAY002", "web.WEB001"]),
        (["--root", "api"], ["demo.ARC002", "demo.PAY002"]),
        (["demo.PAY"], ["demo.PAY002"]),
        (["--stage", "s"], ["demo.ARC002", "demo.PAY002", "web.WEB001"]),
    ],
    ids=["none", "root", "reference", "stage"],
)
def test_not_selected_limits_any_view_to_the_rules_that_nothing_selects(
    wio: Wio, args: list[str], codes: list[str]
) -> None:
    """AC-2: the candidates follow the roots of the view."""
    # Given the repository with a ruleset `web` that no root reaches
    _repo(wio, web=True)

    # When the command runs with `--not-selected` on the view
    output = wio.run(["rules", "list", *args, "--not-selected"])

    # Then it shows the rules that nothing selects among the candidates
    assert list(shown(output)) == codes
    assert "filter: not selected" in header(output)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--root", "api", "--path", "src/x.py"], "--path"),
        (["Docs"], "Docs"),
        (["--preset", "demo.recommended"], "--preset"),
    ],
    ids=["conflict", "reference", "option"],
)
def test_a_refusal_prints_nothing_whichever_leaf_raises_it(
    wio: Wio, args: list[str], message: str
) -> None:
    """AC-3: exit 2, a message on standard error and nothing on standard output."""
    # Given the repository
    _repo(wio)

    # When the command runs
    output = wio.run(["rules", "list", *args])

    # Then it exits 2, says why and prints nothing on standard output
    assert output.exit_code == 2
    assert message in output.stderr
    assert not output.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_fault_in_the_rules_is_refused_before_any_output(wio: Wio) -> None:
    """AC-3: a duplicate code exits 2 and nothing is printed on standard output."""
    # Given the repository and a ruleset `bad` that holds two rules of one code
    _repo(wio, bad=True)

    # When the command runs
    output = wio.run(["rules", "list", "demo.all"])

    # Then it exits 2, names the code and prints nothing on standard output
    assert output.exit_code == 2
    assert "BAD001" in output.stderr
    assert not output.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_json_holds_the_same_listing_as_the_text(wio: Wio) -> None:
    """AC-4: the header keys, the references and the explanation of each rule."""
    # Given the repository
    _repo(wio)
    args = ["rules", "list", "demo.all", "--work", WORK, "--stage", "s", "--explain"]

    # When the command runs as text and with `--json`
    text = wio.run(args)
    as_json = wio.run([*args, "--json"])

    # Then the document has the header keys, the reference, and each rule with
    # the explanation that the text states
    found = json.loads(as_json.stdout)
    assert list(found)[:7] == [
        "view",
        "work",
        "layers",
        "roots",
        "stage",
        "references",
        "not_selected",
    ]
    assert found["references"] == ["demo.all"]
    blocks = _blocks(text)
    assert [r["code"] for r in found["rules"]] == list(blocks)
    for entry in found["rules"]:
        lines = blocks[entry["code"]]
        origins = [line for line in lines if line.startswith("from:")]
        assert len(origins) == len(entry["origins"])
        assert any(line.startswith("out:") for line in lines) == (
            entry["reason"] is not None
        )
