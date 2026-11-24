# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio rules list`, which shows the rules a view is given."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.rules.support import (
    BARE,
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
    from tests.acceptance.dsl.wio import Wio


def _repo(wio: Wio, *, ui: bool = False) -> None:
    """Start the repository of AC-2, and with `ui` that of AC-4.

    Args:
        wio: The facade.
        ui: Whether to add the root `ui` and the stage `t` that selects it.
    """
    wio.fixture(BASE)
    config = (
        'rules_always_include = ["process.FIX001"]\n'
        '[roots.api]\npaths = ["src/api"]\nrule_presets = ["demo.arc"]\n'
        "[rulesets.process]\nroot_independent = true\n"
        '[stages.s]\ngoal = "g"\nrules_include = ["demo.PAY001", "web.WEB001"]\n'
        '[stages.x]\ngoal = "g"\nrules_exclude = ["demo.ARC002"]\n'
    )
    if ui:
        config += '[roots.ui]\npaths = ["src/ui"]\nrule_presets = ["web.core"]\n'
        config += '[stages.t]\ngoal = "g"\nroots = ["ui"]\n'
        config += '[stages.e]\ngoal = "g"\n'
    wio.put(".agents/wio/config.toml", config.encode())
    demo = '[families]\nARC = "A"\nPAY = "P"\n'
    demo += '[rule_presets.arc]\nrules_include = ["ARC"]\n'
    web = '[families]\nWEB = "W"\n[rule_presets.core]\nrules_include = ["WEB001"]\n'
    ruleset(wio, "demo", demo, {"ARC001": "keep", "ARC002": "name", "PAY001": "pay"})
    ruleset(wio, "web", web, {"WEB001": "page"})
    ruleset(wio, "process", '[families]\nFIX = "F"\n', {"FIX001": "fix"})
    work(wio, WORK, 'roots = ["api"]\n')
    work(wio, BARE, "")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_without_a_selector_every_rule_is_listed_with_no_layers(wio: Wio) -> None:
    """AC-1: the header, a blank line and a block for each rule."""
    # Given rules with a description, with a body only and with an empty body
    wio.fixture(BASE)
    wio.put(f"{RULES}/demo/ruleset.toml", b'[families]\nARC = "A"\nPAY = "P"\n')
    wio.put(
        f"{RULES}/demo/ARC001-keep-it-small.md",
        rule(
            "ARC001",
            "keep-it-small",
            "Long body.\n",
            'description = "A rule is one instruction."\n',
        ),
    )
    wio.put(
        f"{RULES}/demo/PAY001-pay-first.md",
        rule("PAY001", "pay-first", "Pay the invoice first.\n"),
    )
    wio.put(f"{RULES}/web/ruleset.toml", b'[families]\nWEB = "W"\n')
    wio.put(f"{RULES}/web/WEB001-web-rule.md", rule("WEB001", "web-rule", ""))

    # When `wio rules list` runs
    output = wio.run(["rules", "list"])

    # Then the output is the header, a blank line and the three blocks, with a
    # blank line between one block and the next
    assert output.stdout == (
        "view: every rule\n"
        "layers: none\n"
        "roots: not applied\n"
        "\n"
        "demo.ARC001  keep-it-small\n"
        "             A rule is one instruction.\n"
        "\n"
        "demo.PAY001  pay-first\n"
        "             Pay the invoice first.\n"
        "\n"
        "web.WEB001   web-rule\n"
    )
    assert output.exit_code == 0


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("args", "view"),
    [
        (["--root", "api"], "root api"),
        (["--path", "src/api/app.py"], "file src/api/app.py"),
        (["--work", WORK], f"Work {WORK}"),
    ],
    ids=["root", "path", "work"],
)
def test_a_root_a_path_or_a_work_gives_the_rules_that_apply(
    wio: Wio, args: list[str], view: str
) -> None:
    """AC-2: the rules of `api` and the always include, under the header."""
    # Given the repository and a Work in `api`
    _repo(wio)

    # When `wio rules list` runs with the selector
    output = wio.run(["rules", "list", *args])

    # Then the rules of `api` and `process.FIX001` are shown, and the header says
    # which layers and roots applied
    assert shown(output) == {
        "demo.ARC001": "api",
        "demo.ARC002": "api",
        "process.FIX001": "every root",
    }
    assert header(output) == [
        f"view: {view}",
        "layers: roots, always fields",
        "roots: api",
    ]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_stage_adds_its_layer_and_without_roots_nothing_is_cut(wio: Wio) -> None:
    """AC-3: roots not applied, then with a root the stage's rules join."""
    # Given the repository and a stage `s` that includes `PAY001` and `WEB001`
    _repo(wio)

    # When `--stage s` and `--root api --stage s` run
    alone = wio.run(["rules", "list", "--stage", "s"])
    both = wio.run(["rules", "list", "--root", "api", "--stage", "s"])

    # Then the first lists the roots that reach each rule, and the second adds
    # `PAY001` to the rules of `api` and cuts `WEB001`
    assert shown(alone) == {
        "demo.PAY001": "api",
        "process.FIX001": "every root",
        "web.WEB001": "none",
    }
    assert header(alone) == [
        "view: stage s",
        "layers: stage, always fields",
        "roots: not applied",
    ]
    assert list(shown(both)) == [
        "demo.ARC001",
        "demo.ARC002",
        "demo.PAY001",
        "process.FIX001",
    ]
    assert "stage: s" in header(both)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_work_alone_gives_its_roots_and_the_stage_decides_which_count(
    wio: Wio,
) -> None:
    """AC-4: the Work's roots, or those of the stage that has its own."""
    # Given the repository with the root `ui` and the stages `e` and `t`
    _repo(wio, ui=True)

    # When `--work`, `--work --stage e` and `--work --stage t` run
    plain = wio.run(["rules", "list", "--work", WORK])
    own = wio.run(["rules", "list", "--work", WORK, "--stage", "e"])
    chosen = wio.run(["rules", "list", "--work", WORK, "--stage", "t"])

    # Then the first two list the rules of `api`, and the third those of `ui`
    assert list(shown(plain)) == ["demo.ARC001", "demo.ARC002", "process.FIX001"]
    assert list(shown(own)) == list(shown(plain))
    assert list(shown(chosen)) == ["process.FIX001", "web.WEB001"]
    assert "roots: ui" in header(chosen)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_rule_that_is_out_is_not_listed(wio: Wio) -> None:
    """AC-5: the rule that the stage excludes is left out of the listing."""
    # Given the repository and the stage `x`, which excludes `demo.ARC002`
    _repo(wio)

    # When `wio rules list --root api --stage x` runs
    output = wio.run(["rules", "list", "--root", "api", "--stage", "x"])

    # Then `demo.ARC002` is not in the output
    assert "demo.ARC002" not in shown(output)
    assert "demo.ARC001" in shown(output)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--root", "api", "--path", "src/x.py"], "--path"),
        pytest.param(["--stage", "none"], "none"),
        pytest.param(["--root", "none"], "none"),
        pytest.param(["--work", "none"], "none"),
        pytest.param(["--work", BARE], BARE),
        pytest.param(["--path", "../x.py"], "outside"),
    ],
    ids=["conflict", "stage", "root", "work", "no roots", "outside"],
)
def test_a_selector_that_cannot_be_used_is_refused(
    wio: Wio, args: list[str], message: str
) -> None:
    """AC-6: exit 2, a message on standard error and nothing on standard output."""
    # Given the repository and a Work that lists no roots
    _repo(wio)

    # When `wio rules list` runs with the selector
    output = wio.run(["rules", "list", *args])

    # Then it exits 2, names the cause and prints nothing on standard output
    assert output.exit_code == 2
    assert message in output.stderr
    assert not output.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_text_is_a_header_and_indented_blocks(wio: Wio) -> None:
    """AC-7: padded first lines, details under the name, a final newline."""
    # Given the repository, whose longest code is `process.FIX001`
    _repo(wio)

    # When `wio rules list --root api` runs
    output = wio.run(["rules", "list", "--root", "api"])

    # Then the header comes first, every first line pads its code to the width of
    # `process.FIX001` and each detail is indented to the name
    lines = output.stdout.splitlines()
    assert lines[3] == ""
    assert lines[4].startswith("demo.ARC001   ")
    assert lines[5] == " " * 16 + "Body."
    assert output.stdout.endswith("\n")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_json_is_one_line_with_the_header_and_the_rules(wio: Wio) -> None:
    """AC-8: the same rules as the text, with the header keys in order."""
    # Given the repository with the stage `s`
    _repo(wio)

    # When `wio rules list --work W --stage s` runs as text and as JSON
    text = wio.run(["rules", "list", "--work", WORK, "--stage", "s"])
    as_json = wio.run(["rules", "list", "--work", WORK, "--stage", "s", "--json"])

    # Then the document is one line with the keys in order and the same rules
    assert as_json.stdout.count("\n") == 1
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
    assert (found["work"], found["roots"], found["stage"]) == (WORK, ["api"], "s")
    assert (found["references"], found["not_selected"]) == ([], False)
    assert list(found)[-1] == "rules"
    assert [rule["code"] for rule in found["rules"]] == list(shown(text))


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_boundaries_of_a_listing(wio: Wio) -> None:
    """AC-12: no rules, a path in no root, and a listing without layers."""
    # Given a repository with no rules
    wio.fixture(BASE)

    # When `wio rules list` runs as text and as JSON
    text = wio.run(["rules", "list"])
    as_json = wio.run(["rules", "list", "--json"])

    # Then the text is the header and a blank line, and the JSON has no rule
    assert text.stdout == "view: every rule\nlayers: none\nroots: not applied\n\n"
    assert json.loads(as_json.stdout)["rules"] == []


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_path_in_no_root_applies_no_root(wio: Wio) -> None:
    """AC-12: `roots: none` and only the rule that is independent of roots."""
    # Given the repository and a file that no root contains
    _repo(wio)
    wio.put("docs/readme.md", b"x\n")

    # When `wio rules list --path docs/readme.md` runs
    output = wio.run(["rules", "list", "--path", "docs/readme.md"])

    # Then the roots are none and only `process.FIX001` is shown
    assert "roots: none" in header(output)
    assert shown(output) == {"process.FIX001": "every root"}


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_listing_without_layers_has_no_decision_in_json(wio: Wio) -> None:
    """AC-12: `roots` and `root_independent` are `null` and `included` is true."""
    # Given the repository
    _repo(wio)

    # When `wio rules list --json` runs
    found = json.loads(wio.run(["rules", "list", "--json"]).stdout)

    # Then every rule has null roots and root independence, and is included
    assert found["rules"]
    for entry in found["rules"]:
        assert (entry["roots"], entry["root_independent"], entry["included"]) == (
            None,
            None,
            True,
        )


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_command_is_declared_and_finds_the_works(wio: Wio) -> None:
    """AC-13: the help names the flags, and `--work` finds a Work of the repository."""
    # Given the repository with a Work `W` in `api`
    _repo(wio)

    # When `wio rules list --help` and `wio rules list --work W` run
    helped = wio.run(["rules", "list", "--help"])
    listed = wio.run(["rules", "list", "--work", WORK])

    # Then the help names every flag and the second lists the rules of `api`
    for flag in ("--root", "--path", "--work", "--stage", "--not-selected"):
        assert flag in helped.stdout
    assert "--explain" in helped.stdout
    assert "--json" in helped.stdout
    assert "demo.ARC001" in shown(listed)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_path_with_a_stage_applies_the_roots_that_contain_it(wio: Wio) -> None:
    """AC-14: the same rules as `--root api --stage s`, with the file's header."""
    # Given the repository and the stage `s`
    _repo(wio)

    # When `wio rules list --path src/api/app.py --stage s` runs
    output = wio.run(["rules", "list", "--path", "src/api/app.py", "--stage", "s"])

    # Then the layers are the three and the rules are those of the root and stage
    assert header(output) == [
        "view: file src/api/app.py",
        "layers: roots, stage, always fields",
        "roots: api",
        "stage: s",
    ]
    assert list(shown(output)) == [
        "demo.ARC001",
        "demo.ARC002",
        "demo.PAY001",
        "process.FIX001",
    ]
