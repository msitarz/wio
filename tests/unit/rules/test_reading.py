# SPDX-License-Identifier: Apache-2.0
"""Tests of the reader of a rule file, which runs on text alone."""

from pathlib import PurePosixPath

import pytest

from wio.models.rule import Rule
from wio.rules import RuleReading, read_rule

_PATH = PurePosixPath(".agents/wio/rules/demo/ARC001-keep-it-small.md")
_FILE = str(_PATH)


def _read(text: str) -> RuleReading:
    """Read a text as a rule of the ruleset `demo` at the usual path.

    Args:
        text: The text of the file.

    Returns:
        What the reader gave.
    """
    return read_rule("demo", _PATH, text)


def _block(*keys: str) -> str:
    """Write a comment block that holds the given lines of TOML.

    Args:
        *keys: The lines between the opening and the closing of the block.

    Returns:
        The block, on lines 1 to `len(keys) + 2`.
    """
    return "\n".join(["<!-- wio", *keys, "-->"]) + "\n"


def _valid(**keys: str) -> str:
    """Write a rule file that has a code, a name and a one-line body.

    Args:
        **keys: The keys to write as TOML values, which replace the default
            `code` and `name` or add a `description`.

    Returns:
        The text of the file.
    """
    values = {"code": '"ARC001"', "name": '"keep-it-small"', **keys}
    return _block(*(f"{key} = {value}" for key, value in values.items())) + "\nBody.\n"


def _front_matter(*keys: str) -> str:
    """Write `+++` front matter that holds the given lines of TOML.

    Args:
        *keys: The lines between the delimiters, `wio = 1` first.

    Returns:
        The front matter and a one-line body.
    """
    return "\n".join(["+++", "wio = 1", *keys, "+++"]) + "\n\nBody.\n"


def _kinds(reading: RuleReading) -> list[tuple[str, str]]:
    """List the severity and the place of each diagnostic.

    Args:
        reading: What the reader gave.

    Returns:
        A pair for each diagnostic.
    """
    return [(d.severity, d.where) for d in reading.diagnostics]


def test_a_marked_file_is_read_into_a_rule() -> None:
    """AC-1: the code, name, description, summary and body of a rule."""
    # Given a rule file with a described block, a body of two paragraphs
    text = (
        _block(
            'code = "ARC001"',
            'name = "keep-it-small"',
            'description = "A rule is one instruction."',
        )
        + "\nState one instruction\nin each rule.\n\n"
        + "Why: a long rule hides several decisions.\n"
    )

    # When it is read as a rule of the ruleset `demo`
    reading = _read(text)

    # Then the rule has its parts, its body starts on line 7, and nothing is
    # reported
    assert reading.rule == Rule(
        ruleset="demo",
        code="ARC001",
        name="keep-it-small",
        description="A rule is one instruction.",
        summary="State one instruction in each rule.",
        body="State one instruction\nin each rule.\n\n"
        "Why: a long rule hides several decisions.",
        body_line=7,
        path=_PATH,
    )
    assert reading.diagnostics == ()


def test_a_rule_without_a_description_has_none() -> None:
    """AC-1: the description is optional."""
    # Given a block that holds only a code and a name
    text = _block('code = "ARC002"', 'name = "other-rule"') + "\nBody.\n"

    # When it is read
    reading = _read(text)

    # Then the rule has no description
    assert reading.rule is not None
    assert reading.rule.description is None


def test_either_block_form_gives_the_same_rule() -> None:
    """AC-2: a comment block and `+++` front matter with `wio = 1` read alike."""
    # Given two texts with the same keys and body in the two forms
    comment = (
        _block("wio = 1", 'code = "ARC001"', 'name = "keep-it-small"') + "\nBody.\n"
    )
    front = _front_matter('code = "ARC001"', 'name = "keep-it-small"')

    # When each is read as a rule of `demo` at the same path
    first, second = _read(comment), _read(front)

    # Then the two rules are equal and neither has a diagnostic
    assert first.rule is not None
    assert first.rule.body == "Body."
    assert first.rule == second.rule
    assert first.diagnostics == second.diagnostics == ()


@pytest.mark.parametrize(
    ("key", "value", "read"),
    [
        ("code", '"ARC001"', True),
        ("code", '"A1"', True),
        ("code", '"ARC1000"', True),
        ("code", '"arc001"', False),
        ("code", '"ARC"', False),
        ("code", '"001"', False),
        ("code", '"ARC-001"', False),
        ("code", '"ARC001a"', False),
        ("name", '"keep-it-small"', True),
        ("name", '"keep-it-small2"', True),
        ("name", '"x"', True),
        ("name", '"Keep-It-Small"', False),
        ("name", '"keep--it"', False),
        ("name", '"keep-it-"', False),
        ("name", '"-keep"', False),
        ("name", '"2fast"', False),
        ("name", '"keep_it"', False),
        ("description", '"One line."', True),
        ("description", '"  "', False),
        ("description", '"two\\nlines"', False),
        ("description", "3", False),
        ("code", "3", False),
        ("name", "3", False),
    ],
)
def test_every_key_has_its_form_and_its_type(
    key: str,
    value: str,
    read: bool,  # noqa: FBT001
) -> None:
    """AC-3: a code, a name and a description of another form or type is an error."""
    # Given a file whose key has the TOML value of the case
    text = _valid(**{key: value})

    # When it is read
    reading = _read(text)

    # Then a value of the form is read, and any other is one error that names the
    # file and leaves the rule out
    assert (reading.rule is not None) is read
    if not read:
        assert [s for s, _ in _kinds(reading)] == ["error"]
        assert reading.diagnostics[0].where.startswith(_FILE)


@pytest.mark.parametrize(
    ("keys", "errors"),
    [
        (('name = "keep-it-small"',), 1),
        (('code = "ARC001"',), 1),
        ((), 2),
    ],
)
def test_missing_keys_are_reported_together(keys: tuple[str, ...], errors: int) -> None:
    """AC-4: each missing key is one error that names the file."""
    # Given a block without a code, without a name and with neither
    text = _block(*keys) + "\nBody.\n"

    # When it is read
    reading = _read(text)

    # Then there is one error for each missing key and no rule
    assert _kinds(reading) == [("error", _FILE)] * errors
    assert reading.rule is None


def test_an_error_and_a_warning_are_both_reported() -> None:
    """AC-4: a bad code and an unknown key give an error and a warning."""
    # Given a block with a code of `arc001`, a valid name and a key `owner`
    text = _block('code = "arc001"', 'name = "keep-it-small"', 'owner = "me"')

    # When it is read
    reading = _read(text)

    # Then there is one error and one warning, and no rule
    assert sorted(s for s, _ in _kinds(reading)) == ["error", "warning"]
    assert [w for s, w in _kinds(reading) if s == "warning"] == [_FILE]
    by_severity = {d.severity: d.message for d in reading.diagnostics}
    assert "`code`" in by_severity["error"]
    assert "`owner`" in by_severity["warning"]
    assert reading.rule is None


@pytest.mark.parametrize(
    ("text", "line"),
    [
        ('<!-- wio\ncode = "ARC001"\nname = "x"\n', 1),
        ('<!-- wio\ncode = "ARC001"\nname = \n-->\n', 3),
    ],
)
def test_a_block_that_cannot_be_read_is_one_error_with_a_line(
    text: str, line: int
) -> None:
    """AC-4: the place is the file's path, `:` and the line of the fault."""
    # Given a comment block that does not close, whose fault is on line 1, and
    # one whose TOML does not parse, whose fault is on line 3

    # When it is read
    reading = _read(text)

    # Then it is one error whose place has the path and that line, and no rule
    assert reading.rule is None
    assert _kinds(reading) == [("error", f"{_FILE}:{line}")]


def test_a_mistyped_key_is_a_warning_that_suggests_the_close_key() -> None:
    """AC-5: `descriptions` is close to `description`, and the rule is read."""
    # Given a block with a code, a name and `descriptions`
    text = _block('code = "ARC001"', 'name = "x"', 'descriptions = "Keep it small."')

    # When it is read
    reading = _read(text)

    # Then one warning names the key and the suggestion, and the rule has no
    # description
    assert _kinds(reading) == [("warning", _FILE)]
    assert "`descriptions`" in reading.diagnostics[0].message
    assert "Did you mean `description`?" in reading.diagnostics[0].message
    assert reading.rule is not None
    assert reading.rule.description is None


def test_a_key_close_to_nothing_is_a_warning_without_a_suggestion() -> None:
    """AC-5: `owner` is close to no key, and the rule is read."""
    # Given a block with a code, a name and `owner`
    text = _block('code = "ARC001"', 'name = "x"', 'owner = "me"')

    # When it is read
    reading = _read(text)

    # Then one warning names the key and suggests none, and the rule is read
    assert _kinds(reading) == [("warning", _FILE)]
    assert "`owner`" in reading.diagnostics[0].message
    assert "Did you mean" not in reading.diagnostics[0].message
    assert reading.rule is not None


@pytest.mark.parametrize(
    "text",
    [
        "Just a paragraph.\n",
        "\n" + _block('code = "ARC001"', 'name = "x"'),
        '+++\ntitle = "x"\n+++\n\nBody.\n',
    ],
)
def test_a_file_that_is_not_marked_is_not_a_rule(text: str) -> None:
    """AC-6: no block on the first line, or front matter without `wio`."""
    # Given a text with no block, a block on its second line and foreign front
    # matter

    # When it is read
    reading = _read(text)

    # Then there is no rule and no diagnostic
    assert reading == RuleReading(None, ())


@pytest.mark.parametrize(
    "text",
    [
        '+++\nwio = 2\ncode = "ARC001"\n+++\n',
        '+++\nwio = "1"\ncode = "ARC001"\n+++\n',
        '+++\nwio = 1\ncode = "ARC001"\n',
    ],
)
def test_a_wio_key_the_reader_cannot_accept_is_an_error(text: str) -> None:
    """AC-6: the wrong version, a string and an unclosed block."""
    # Given front matter with `wio = 2`, `wio = "1"` and `wio = 1` unclosed

    # When it is read
    reading = _read(text)

    # Then it is one error and no rule
    assert reading.rule is None
    assert [s for s, _ in _kinds(reading)] == ["error"]


def test_the_body_is_cut_from_the_text_without_its_blank_lines() -> None:
    """AC-7: leading and trailing blank lines go, inner ones and indents stay."""
    # Given a block followed by blank lines, two paragraphs and blank lines
    text = (
        _block('code = "ARC001"', 'name = "x"')
        + "\n   \n  Keep it small.\n\nWhy: it is easier to check.\n\n\n"
    )

    # When it is read
    reading = _read(text)

    # Then the body keeps the leading spaces and the blank line between, starts on
    # line 7 after the blank line and the line of spaces, and the summary is the
    # first paragraph
    assert reading.rule is not None
    assert reading.rule.body == "  Keep it small.\n\nWhy: it is easier to check."
    assert reading.rule.summary == "Keep it small."
    assert reading.rule.body_line == 7


def test_a_summary_joins_the_stripped_lines_of_the_first_paragraph() -> None:
    """AC-7: three lines, the second indented, joined with single spaces."""
    # Given a first paragraph of three lines, the second indented
    text = _block('code = "ARC001"', 'name = "x"') + "\nOne\n    two\nthree\n"

    # When it is read
    reading = _read(text)

    # Then the summary joins the stripped lines with single spaces
    assert reading.rule is not None
    assert reading.rule.summary == "One two three"


def test_a_file_with_no_body_has_an_empty_body_after_the_block() -> None:
    """AC-7: empty body and summary, `body_line` is the line after the block."""
    # Given a block followed by nothing but blank lines
    text = _block('code = "ARC001"', 'name = "x"') + "\n\n  \n"

    # When it is read
    reading = _read(text)

    # Then the body and summary are empty, the body starts on line 5, and
    # nothing is reported
    assert reading.rule is not None
    assert (reading.rule.body, reading.rule.summary) == ("", "")
    assert reading.rule.body_line == 5
    assert reading.diagnostics == ()


def test_windows_line_endings_stay_in_the_body_but_not_in_the_summary() -> None:
    """AC-7: the summary holds no carriage return and the body keeps CRLF."""
    # Given a text whose lines end in CRLF and whose first paragraph has two lines
    text = _block('code = "ARC001"', 'name = "x"').replace("\n", "\r\n")
    text += "\r\nFirst line\r\nsecond line\r\n\r\nWhy.\r\n"

    # When it is read
    reading = _read(text)

    # Then the summary joins two lines with one space and the body keeps its CRLF
    assert reading.rule is not None
    assert reading.rule.summary == "First line second line"
    assert reading.rule.body == "First line\r\nsecond line\r\n\r\nWhy."


def test_rules_read_from_the_same_text_are_equal_values() -> None:
    """AC-8: the same text gives equal rules, another code gives another key."""
    # Given the same text read twice and the same text with another code
    first, second = _read(_valid()).rule, _read(_valid()).rule
    other = _read(_valid(code='"ARC002"')).rule

    # When they are used as keys of one mapping
    assert first is not None
    assert other is not None
    keys = {first: 1, second: 2, other: 3}

    # Then the first two share one key and the third is a different one
    assert len(keys) == 2
    with pytest.raises(AttributeError):
        first.name = "other"  # type: ignore[misc]
    assert first == second
    assert hash(first) == hash(second)
    assert first != other
