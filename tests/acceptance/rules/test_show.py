# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio rules show`, which prints one rule by its code."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.rules.support import BASE, RULES, rule, ruleset

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

CONFIG = '[rulesets.demo]\nalias = "d"\n'
MANIFEST = (
    '[families]\nARC = "A"\n[rule_presets.recommended]\nrules_include = ["ARC"]\n'
)
FILE = f"{RULES}/demo/ARC001-keep-it-small.md"
BODY = (
    "State one instruction in each rule.\n\nWhy: a long rule hides several decisions."
)
_BOTH = pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)


def _repo(wio: Wio) -> None:
    """Start the repository: `demo` with `ARC001`, `ARC002` and the alias `d`.

    Args:
        wio: The facade.
    """
    wio.fixture(BASE)
    wio.put(".agents/wio/config.toml", CONFIG.encode())
    ruleset(wio, "demo", MANIFEST, {"ARC002": "other-rule"})
    wio.put(
        FILE,
        rule(
            "ARC001",
            "keep-it-small",
            body=BODY + "\n",
            extra='description = "A rule is one instruction."\n',
        ),
    )


@_BOTH
def test_a_rule_is_shown_with_its_header_and_its_body(wio: Wio) -> None:
    """AC-1: the name, the description, the file, a blank line and the body."""
    # Given a rule with a description and a body of two paragraphs
    _repo(wio)

    # When it is shown
    output = wio.run(["rules", "show", "demo.ARC001"])

    # Then the header is indented to the name and the body follows a blank line
    assert output.exit_code == 0
    assert output.stdout == (
        "demo.ARC001  keep-it-small\n"
        "             A rule is one instruction.\n"
        f"             file: {FILE}\n"
        f"\n{BODY}\n"
    )


@_BOTH
def test_a_rule_without_a_description_or_a_body_prints_only_its_header(
    wio: Wio,
) -> None:
    """AC-2: no description line, no blank line and no body."""
    # Given a rule with no description and an empty body
    _repo(wio)
    wio.put(f"{RULES}/demo/ARC002-other-rule.md", rule("ARC002", "other-rule", ""))

    # When it is shown
    output = wio.run(["rules", "show", "demo.ARC002"])

    # Then only the name and the file line are printed
    assert output.stdout == (
        "demo.ARC002  other-rule\n"
        f"             file: {RULES}/demo/ARC002-other-rule.md\n"
    )


@_BOTH
def test_the_body_keeps_its_indentation(wio: Wio) -> None:
    """AC-3: two leading spaces."""
    # Given a body that starts with two spaces
    _repo(wio)
    wio.put(f"{RULES}/demo/ARC002-other-rule.md", rule("ARC002", "other-rule", "  a\n"))

    # When it is shown
    output = wio.run(["rules", "show", "demo.ARC002"])

    # Then the body keeps its spaces and one line feed ends it
    assert output.stdout.endswith("\n\n  a\n")


# The CLI channel decodes the output as text, which folds CRLF into LF, so only
# the channel that reads the streams as they are can see the endings.
@pytest.mark.channels(Channel.IN_PROCESS)
def test_the_body_keeps_its_line_endings(wio: Wio) -> None:
    """AC-3: CRLF between the lines of the body."""
    # Given a file with CRLF line endings
    _repo(wio)
    crlf = rule("ARC003", "crlf", "one\ntwo\n").replace(b"\n", b"\r\n")
    wio.put(f"{RULES}/demo/ARC003-crlf.md", crlf)

    # When it is shown
    output = wio.run(["rules", "show", "demo.ARC003"])

    # Then the body keeps its CRLF and one line feed ends it
    assert output.stdout.endswith("\n\none\r\ntwo\n")


@_BOTH
def test_an_alias_is_accepted_and_the_canonical_name_is_shown(wio: Wio) -> None:
    """AC-4: `d.ARC001` shows `demo.ARC001`."""
    # Given the alias `d` of `demo`
    _repo(wio)

    # When the rule is shown by the alias
    output = wio.run(["rules", "show", "d.ARC001"])

    # Then it is shown as `demo.ARC001`
    assert output.stdout.startswith("demo.ARC001  keep-it-small\n")
    assert "d.ARC001" not in output.stdout.replace("demo.ARC001", "")


@_BOTH
@pytest.mark.parametrize(
    ("reference", "message"),
    [
        ("demo.ARC", "`demo.ARC` is a family and `show` takes a rule's code"),
        ("demo.recommended", "`demo.recommended` is a rule preset"),
        ("demo.all", "`demo.all` is a rule preset"),
        ("ARC001", "`ARC001` has no ruleset"),
        ("Docs", "`Docs` is not a reference"),
        ("nope.ARC001", "No ruleset is `nope`"),
        ("demo.ARC999", "`ARC001` and `ARC002`"),
        ("demo.arc001", "form of a rule preset name"),
    ],
)
def test_a_reference_that_is_not_one_rules_code_is_refused(
    wio: Wio, reference: str, message: str
) -> None:
    """AC-5: exit 2, the cause on standard error and nothing on standard output."""
    # Given `demo` with `ARC001` and `ARC002` and a rule preset
    _repo(wio)

    # When the reference is shown
    output = wio.run(["rules", "show", reference])

    # Then it exits 2, says what is wrong and prints nothing
    assert output.exit_code == 2
    assert message in output.stderr
    assert not output.stdout


@_BOTH
def test_a_warning_refuses_nothing_and_an_error_anywhere_does(wio: Wio) -> None:
    """AC-6: an unknown key is shown past, a block that does not close refuses."""
    # Given a valid rule whose block has an unknown key
    _repo(wio)
    wio.put(FILE, rule("ARC001", "keep-it-small", extra='owner = "x"\n'))

    # When it is shown, and again with a fault in another ruleset
    allowed = wio.run(["rules", "show", "demo.ARC001"])
    ruleset(wio, "bad", '[families]\nARC = "A"\n', {})
    wio.put(f"{RULES}/bad/ARC001-open.md", b"<!-- wio\n")
    refused = wio.run(["rules", "show", "demo.ARC001"])
    unjudged = wio.run(["rules", "show", "Docs"])

    # Then the first shows the rule and the second refuses
    assert (allowed.exit_code, allowed.stdout.startswith("demo.ARC001")) == (0, True)
    assert (refused.exit_code, refused.stdout) == (2, "")
    assert "ARC001-open.md" in refused.stderr
    assert "ARC001-open.md" in unjudged.stderr


@_BOTH
def test_the_json_is_one_line_with_a_fixed_order(wio: Wio) -> None:
    """AC-7: the fields in order, `null` for no description."""
    # Given a rule with a description and a rule with neither it nor a body
    _repo(wio)
    wio.put(f"{RULES}/demo/ARC002-other-rule.md", rule("ARC002", "other-rule", ""))

    # When each is shown as JSON
    first = wio.run(["rules", "show", "demo.ARC001", "--json"])
    second = wio.run(["rules", "show", "demo.ARC002", "--json"])

    # Then each is one line with the fields in order and the body without a
    # final line feed
    assert first.stdout.count("\n") == second.stdout.count("\n") == 1
    found = json.loads(first.stdout)
    assert list(found) == ["code", "name", "description", "summary", "body", "path"]
    assert found == {
        "code": "demo.ARC001",
        "name": "keep-it-small",
        "description": "A rule is one instruction.",
        "summary": "State one instruction in each rule.",
        "body": BODY,
        "path": FILE,
    }
    bare = json.loads(second.stdout)
    assert (bare["description"], bare["body"]) == (None, "")


@_BOTH
def test_the_output_is_deterministic_and_nothing_is_written(wio: Wio) -> None:
    """AC-8: two runs give equal bytes and leave the repository as it was."""
    # Given one repository
    _repo(wio)
    before = wio.fingerprint(".")

    # When the rule is shown twice, as text and as JSON
    texts = [wio.run(["rules", "show", "demo.ARC001"]) for _ in range(2)]
    jsons = [wio.run(["rules", "show", "demo.ARC001", "--json"]) for _ in range(2)]

    # Then the runs agree, say something, and no file changed
    assert texts[0].stdout == texts[1].stdout != ""
    assert jsons[0].stdout == jsons[1].stdout != ""
    assert wio.fingerprint(".") == before
