# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio rules check`, which joins every fault of the rules."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

BASE = "rules/base"
RULES = ".agents/wio/rules"
PASSES = "The rules pass.\n"
OWNER = ".agents/wio/rules/demo/ARC001-keep-it-small.md"
LOUD = ".agents/wio/rules/demo/ZZZ001-loud-rule.md"


def _config(
    *, reference: str = "demo.XYZ", rulesets: tuple[str, ...] = ("demo",)
) -> str:
    """Build a config whose root selects rulesets and whose stage has a reference.

    Args:
        reference: The entry of the stage's `rules_include`.
        rulesets: The rulesets that the root's rule preset selects.

    Returns:
        The text of the config.
    """
    presets = ", ".join(f'"{name}.all"' for name in rulesets)
    return (
        f'[roots.code]\npaths = ["src"]\nrule_presets = [{presets}]\n\n'
        f'[stages.s]\ngoal = "Do it."\nrules_include = ["{reference}"]\n'
    )


def _rule(code: str, name: str, *, extra: str = "", body: str = "Keep it.\n") -> bytes:
    """Build a rule file.

    Args:
        code: The rule's code.
        name: The rule's name.
        extra: Lines for the metadata block, after the name.
        body: What follows the block and a blank line.

    Returns:
        The bytes of the file.
    """
    block = f'<!-- wio\ncode = "{code}"\nname = "{name}"\n{extra}-->\n\n'
    return (block + body).encode()


def _manifest(*families: str, top: str = "", extra: str = "") -> bytes:
    """Build the manifest of a ruleset.

    Args:
        families: The codes of the families declared, each titled `Family`.
        top: Further keys, before the tables.
        extra: Further TOML, after the families.

    Returns:
        The bytes of the file.
    """
    declared = "".join(f'{code} = "Family"\n' for code in families or ("ARC",))
    return f"{top}[families]\n{declared}{extra}".encode()


def _demo(wio: Wio, *, reference: str, loud: bool = True, owner: bool = True) -> None:
    """Start the repository of AC-1.

    Args:
        wio: The facade.
        reference: The entry of the stage's `rules_include`.
        loud: Whether `ZZZ001` has a heading in its body.
        owner: Whether `ARC001` has the unknown key `owner`.
    """
    wio.put(".agents/wio/config.toml", _config(reference=reference).encode())
    wio.put(f"{RULES}/demo/ruleset.toml", _manifest("ARC", "ZZZ"))
    extra = 'owner = "me"\n' if owner else ""
    wio.put(OWNER, _rule("ARC001", "keep-it-small", extra=extra))
    body = "# Loud\n\nText.\n" if loud else "Text.\n"
    wio.put(LOUD, _rule("ZZZ001", "loud-rule", body=body))


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_one_report_holds_errors_and_warnings(wio: Wio) -> None:
    """AC-1: three findings, in the shared order, and exit 1 for the error."""
    # Given a ruleset with an unknown key, a heading in a body and a reference to
    # a family that it does not declare
    wio.fixture(BASE)
    _demo(wio, reference="demo.XYZ")

    # When `wio rules check` runs
    output = wio.run(["rules", "check"])

    # Then it prints the two warnings and the error in the order of the places,
    # and exits 1
    assert len(output.lines) == 3
    assert output.lines[0].startswith(f"warning: {OWNER}: ")
    assert output.lines[1].startswith(f"warning: {LOUD}:6: ")
    assert output.lines[2].startswith("error: stages.s.rules_include[0]: ")
    assert "demo.XYZ" in output.lines[2]
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_warnings_alone_and_nothing_exit_0(wio: Wio) -> None:
    """AC-1: warnings print and exit 0, and a clean repository passes."""
    # Given the repository with a valid reference
    wio.fixture(BASE)
    _demo(wio, reference="demo.ARC")

    # When `wio rules check` runs, and again once the key and heading are gone
    warned = wio.run(["rules", "check"])
    _demo(wio, reference="demo.ARC", loud=False, owner=False)
    clean = wio.run(["rules", "check"])

    # Then the first prints the two warnings and the second passes, each exit 0
    assert [line.split(":")[0] for line in warned.lines] == ["warning", "warning"]
    assert warned.exit_code == 0
    assert (clean.stdout, clean.exit_code) == (PASSES, 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_each_fault_is_reported_once(wio: Wio) -> None:
    """AC-2: a fault of the discovery is one line, and the references add none."""
    # Given a rule whose block does not close, a rule and a manifest with an
    # unknown key, and a rule preset that includes `Docs`
    wio.fixture(BASE)
    wio.put(".agents/wio/config.toml", _config(reference="demo.ARC").encode())
    manifest = _manifest(
        top='owner = "me"\n',
        extra='\n[rule_presets.local]\nrules_include = ["Docs"]\n',
    )
    wio.put(f"{RULES}/demo/ruleset.toml", manifest)
    wio.put(f"{RULES}/demo/ARC001-open.md", b'<!-- wio\ncode = "ARC001"\n')
    wio.put(
        f"{RULES}/demo/ARC002-keep-it-small.md",
        _rule("ARC002", "keep-it-small", extra='owner = "me"\n'),
    )

    # When `wio rules check` runs
    output = wio.run(["rules", "check"])

    # Then each of the four faults is one line and nothing else is printed
    kinds = [tuple(line.split(": ")[:2]) for line in output.lines]
    assert len(kinds) == 4
    assert sorted(kinds) == [
        ("error", f"{RULES}/demo/ARC001-open.md:1"),
        ("error", f"{RULES}/demo/ruleset.toml#rule_presets.local.rules_include[0]"),
        ("warning", f"{RULES}/demo/ARC002-keep-it-small.md"),
        ("warning", f"{RULES}/demo/ruleset.toml#owner"),
    ]
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_whole_repository_is_judged(wio: Wio) -> None:
    """AC-3: a ruleset that nothing selects is judged with the others."""
    # Given `used`, which a root selects, and `spare`, which nothing includes
    wio.fixture(BASE)
    wio.put(
        ".agents/wio/config.toml",
        _config(reference="used.ARC", rulesets=("used",)).encode(),
    )
    for name in ("used", "spare"):
        wio.put(f"{RULES}/{name}/ruleset.toml", _manifest())
        wio.put(
            f"{RULES}/{name}/ARC001-a-rule.md",
            _rule("ARC001", "a-rule", extra='owner = "me"\n'),
        )

    # When `wio rules check` runs
    output = wio.run(["rules", "check"])

    # Then it prints a warning for each rule and exits 0
    assert [line.split(": ")[1] for line in output.lines] == [
        f"{RULES}/spare/ARC001-a-rule.md",
        f"{RULES}/used/ARC001-a-rule.md",
    ]
    assert all(line.startswith("warning: ") for line in output.lines)
    assert output.exit_code == 0


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_json_and_the_exit_code_hold(wio: Wio) -> None:
    """AC-4: one array in all three outcomes, with exit 1, 0 and 0."""
    # Given a repository with an error, then one with a warning, then none
    wio.fixture(BASE)
    _demo(wio, reference="demo.XYZ")
    failing = wio.run(["rules", "check", "--json"])
    _demo(wio, reference="demo.ARC", loud=False)
    warning = wio.run(["rules", "check", "--json"])
    _demo(wio, reference="demo.ARC", loud=False, owner=False)

    # When `wio rules check --json` runs on the last
    clean = wio.run(["rules", "check", "--json"])

    # Then each prints one array and the codes are 1, 0 and 0
    assert [(item["severity"]) for item in json.loads(failing.stdout)] == [
        "warning",
        "warning",
        "error",
    ]
    assert failing.exit_code == 1
    assert [item["severity"] for item in json.loads(warning.stdout)] == ["warning"]
    assert warning.exit_code == 0
    assert (clean.stdout, clean.exit_code) == ("[]\n", 0)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_no_rulesets_pass(wio: Wio) -> None:
    """AC-5: a repository with no rulesets passes, as text and as JSON."""
    # Given a repository with a config and no `.agents/wio/rules`
    wio.fixture(BASE)

    # When `wio rules check` runs, with and without `--json`
    text = wio.run(["rules", "check"])
    as_json = wio.run(["rules", "check", "--json"])

    # Then it prints the sentence and `[]`, each exiting 0
    assert (text.stdout, text.exit_code) == (PASSES, 0)
    assert (as_json.stdout, as_json.exit_code) == ("[]\n", 0)
