# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio rules list`, which shows the rules a view is given."""

import json
import re
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.results import Output
    from tests.acceptance.dsl.wio import Wio

BASE = "rules/base"
RULES = ".agents/wio/rules"
WORK = "k3m9xq"
BARE = "n5p7qr"
pytestmark = pytest.mark.xfail(strict=True, reason="wio rules list is not wired")


def _rule(code: str, name: str, body: str = "Body.\n", extra: str = "") -> bytes:
    """Build a rule file.

    Args:
        code: The rule's code.
        name: The rule's name.
        body: What follows the block and a blank line.
        extra: Lines for the block after the name.

    Returns:
        The bytes of the file.
    """
    block = f'<!-- wio\ncode = "{code}"\nname = "{name}"\n{extra}-->\n\n'
    return (block + body).encode()


def _ruleset(wio: Wio, name: str, manifest: str, rules: dict[str, str]) -> None:
    """Write a ruleset.

    Args:
        wio: The facade.
        name: The ruleset's name.
        manifest: The text of its `ruleset.toml`.
        rules: Each rule's code and name.
    """
    wio.put(f"{RULES}/{name}/ruleset.toml", manifest.encode())
    for code, rule_name in rules.items():
        wio.put(f"{RULES}/{name}/{code}-{rule_name}.md", _rule(code, rule_name))


def _work(wio: Wio, work_id: str, roots: str) -> None:
    """Write a Work with the given roots.

    Args:
        wio: The facade.
        work_id: The Work's id.
        roots: The `roots` line of its metadata, or an empty string.
    """
    block = f'<!-- wio\nid = "{work_id}"\n{roots}-->\n\n# A Work\n'
    wio.put(f".agents/wio/works/{work_id}/README.md", block.encode())


def _repo(wio: Wio, *, ui: bool = False) -> None:
    """Start the repository of AC-2, and with `ui` that of AC-4.

    Args:
        wio: The facade.
        ui: Whether to add the root `ui` and the stage `t` that selects it.
    """
    wio.fixture(BASE)
    config = (
        '[roots.api]\npaths = ["src/api"]\nrule_presets = ["demo.arc"]\n'
        "[rulesets.process]\nroot_independent = true\n"
        'rules_always_include = ["process.FIX001"]\n'
        '[stages.s]\ngoal = "g"\nrules_include = ["demo.PAY001", "web.WEB001"]\n'
        '[stages.x]\ngoal = "g"\nrules_exclude = ["demo.ARC002"]\n'
    )
    if ui:
        config += '[roots.ui]\npaths = ["src/ui"]\nrule_presets = ["web.core"]\n'
        config += '[stages.t]\ngoal = "g"\nroots = ["ui"]\n'
    wio.put(".agents/wio/config.toml", config.encode())
    demo = '[families]\nARC = "A"\nPAY = "P"\n'
    demo += '[rule_presets.arc]\nrules_include = ["ARC"]\n'
    web = '[families]\nWEB = "W"\n[rule_presets.core]\nrules_include = ["WEB001"]\n'
    _ruleset(wio, "demo", demo, {"ARC001": "keep", "ARC002": "name", "PAY001": "pay"})
    _ruleset(wio, "web", web, {"WEB001": "page"})
    _ruleset(wio, "process", '[families]\nFIX = "F"\n', {"FIX001": "fix"})
    _work(wio, WORK, 'roots = ["api"]\n')
    _work(wio, BARE, "")


def _shown(output: Output) -> dict[str, str | None]:
    """Read the rules of the text and their `roots:` lines.

    Args:
        output: The result of `wio rules list`.

    Returns:
        Each qualified code with the value of its `roots:` line, or `None`.
    """
    found: dict[str, str | None] = {}
    for line in output.stdout.splitlines():
        if re.match(r"\w+\.[A-Z]+\d+ ", line):
            code = line.split()[0]
            found[code] = None
        elif (match := re.match(r"\s+roots: (.*)", line)) and found:
            found[list(found)[-1]] = match[1]
    return found


def _header(output: Output) -> list[str]:
    """Read the header lines of the text.

    Args:
        output: The result of `wio rules list`.

    Returns:
        The lines before the first blank line.
    """
    return output.stdout.split("\n\n")[0].splitlines()


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_without_a_selector_every_rule_is_listed_with_no_layers(wio: Wio) -> None:
    """AC-1: the header, a blank line and a block for each rule."""
    # Given rules with a description, with a body only and with an empty body
    wio.fixture(BASE)
    wio.put(f"{RULES}/demo/ruleset.toml", b'[families]\nARC = "A"\nPAY = "P"\n')
    wio.put(
        f"{RULES}/demo/ARC001-keep-it-small.md",
        _rule(
            "ARC001",
            "keep-it-small",
            "Long body.\n",
            'description = "A rule is one instruction."\n',
        ),
    )
    wio.put(
        f"{RULES}/demo/PAY001-pay-first.md",
        _rule("PAY001", "pay-first", "Pay the invoice first.\n"),
    )
    wio.put(f"{RULES}/web/ruleset.toml", b'[families]\nWEB = "W"\n')
    wio.put(f"{RULES}/web/WEB001-web-rule.md", _rule("WEB001", "web-rule", ""))

    # When `wio rules list` runs
    output = wio.run(["rules", "list"])

    # Then the output is the header, a blank line and the three blocks
    assert output.stdout == (
        "view: every rule\n"
        "layers: none\n"
        "roots: not applied\n"
        "\n"
        "demo.ARC001  keep-it-small\n"
        "             A rule is one instruction.\n"
        "demo.PAY001  pay-first\n"
        "             Pay the invoice first.\n"
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
    assert _shown(output) == {
        "demo.ARC001": "api",
        "demo.ARC002": "api",
        "process.FIX001": "every root",
    }
    assert _header(output) == [
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
    assert _shown(alone) == {
        "demo.PAY001": "api",
        "process.FIX001": "every root",
        "web.WEB001": "none",
    }
    assert _header(alone) == [
        "view: stage s",
        "layers: stage, always fields",
        "roots: not applied",
    ]
    assert list(_shown(both)) == [
        "demo.ARC001",
        "demo.ARC002",
        "demo.PAY001",
        "process.FIX001",
    ]
    assert "stage: s" in _header(both)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_work_alone_gives_its_roots_and_the_stage_decides_which_count(
    wio: Wio,
) -> None:
    """AC-4: the Work's roots, or those of the stage that has its own."""
    # Given the repository with the root `ui` and the stages `s` and `t`
    _repo(wio, ui=True)

    # When `--work`, `--work --stage s` and `--work --stage t` run
    plain = wio.run(["rules", "list", "--work", WORK])
    own = wio.run(["rules", "list", "--work", WORK, "--stage", "s"])
    chosen = wio.run(["rules", "list", "--work", WORK, "--stage", "t"])

    # Then the first two list the rules of `api`, and the third those of `ui`
    assert list(_shown(plain)) == ["demo.ARC001", "demo.ARC002", "process.FIX001"]
    assert "demo.ARC001" in _shown(own)
    assert list(_shown(chosen)) == ["process.FIX001", "web.WEB001"]
    assert "roots: ui" in _header(chosen)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_rule_that_is_out_is_not_listed(wio: Wio) -> None:
    """AC-5: the rule that the stage excludes is left out of the listing."""
    # Given the repository and the stage `x`, which excludes `demo.ARC002`
    _repo(wio)

    # When `wio rules list --root api --stage x` runs
    output = wio.run(["rules", "list", "--root", "api", "--stage", "x"])

    # Then `demo.ARC002` is not in the output
    assert "demo.ARC002" not in _shown(output)
    assert "demo.ARC001" in _shown(output)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--root", "api", "--path", "src/x.py"], "--path"),
        (["--stage", "none"], "none"),
        (["--root", "none"], "none"),
        (["--work", "none"], "none"),
        (["--work", BARE], BARE),
        (["--path", "../x.py"], "outside"),
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
    assert [rule["code"] for rule in found["rules"]] == list(_shown(text))


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_boundaries_of_a_listing(wio: Wio) -> None:
    """AC-12: no rules, a path in no root, and a listing without layers."""
    # Given a repository with no rules
    wio.fixture(BASE)

    # When `wio rules list` runs as text and as JSON
    text = wio.run(["rules", "list"])
    as_json = wio.run(["rules", "list", "--json"])

    # Then the text is the header and a blank line, and the JSON has no rule
    assert text.stdout.endswith("\n\n")
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
    assert "roots: none" in _header(output)
    assert _shown(output) == {"process.FIX001": "every root"}


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_listing_without_layers_has_no_decision_in_json(wio: Wio) -> None:
    """AC-12: `roots` and `root_independent` are `null` and `included` is true."""
    # Given the repository
    _repo(wio)

    # When `wio rules list --json` runs
    found = json.loads(wio.run(["rules", "list", "--json"]).stdout)

    # Then every rule has null roots and root independence, and is included
    assert found["rules"]
    for rule in found["rules"]:
        assert (rule["roots"], rule["root_independent"], rule["included"]) == (
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
    assert "demo.ARC001" in _shown(listed)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_path_with_a_stage_applies_the_roots_that_contain_it(wio: Wio) -> None:
    """AC-14: the same rules as `--root api --stage s`, with the file's header."""
    # Given the repository and the stage `s`
    _repo(wio)

    # When `wio rules list --path src/api/app.py --stage s` runs
    output = wio.run(["rules", "list", "--path", "src/api/app.py", "--stage", "s"])

    # Then the layers are the three and the rules are those of the root and stage
    assert _header(output)[:2] == [
        "view: file src/api/app.py",
        "layers: roots, stage, always fields",
    ]
    assert list(_shown(output)) == [
        "demo.ARC001",
        "demo.ARC002",
        "demo.PAY001",
        "process.FIX001",
    ]
