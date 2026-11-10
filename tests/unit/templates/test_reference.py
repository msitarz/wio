# SPDX-License-Identifier: Apache-2.0
"""Tests of the rendering of `wio templates directives` in `wio.templates`."""

from json import loads

from wio.formats.directives import DIRECTIVES
from wio.models.directives import DirectiveSpec
from wio.templates import render_reference

TABLE = (
    DirectiveSpec("one", "one", "A meaning.", ("## A <!-- wio: one -->",)),
    DirectiveSpec(
        "two",
        'two=<x> or two="<x>"',
        "The first line.\n\nThe third line.",
        ("## B <!-- wio: two=a -->", '## B <!-- wio: two="a" -->'),
    ),
    DirectiveSpec("three", "three", "No example.", ()),
)


def test_the_human_form_prints_each_entry_of_the_table_as_it_is() -> None:
    """AC-1: a block for each entry, in order, with the table's own fields."""
    # Given a table of entries, one with a meaning of three lines, an empty one
    # between them, one with two examples and one with none
    table = TABLE

    # When it is rendered for a person
    text = render_reference(table, as_json=False)

    # Then each entry is a block of the name, `Syntax:`, the meaning indented by
    # two spaces with its empty line left empty, and an `Example:` line for each
    # example, with one empty line between blocks and none after the last
    assert text == (
        "one\n"
        "  Syntax: one\n"
        "  A meaning.\n"
        "  Example: ## A <!-- wio: one -->\n"
        "\n"
        "two\n"
        '  Syntax: two=<x> or two="<x>"\n'
        "  The first line.\n"
        "\n"
        "  The third line.\n"
        "  Example: ## B <!-- wio: two=a -->\n"
        '  Example: ## B <!-- wio: two="a" -->\n'
        "\n"
        "three\n"
        "  Syntax: three\n"
        "  No example.\n"
    )


def test_the_json_form_is_one_array_of_the_entries_in_order() -> None:
    """AC-2: objects with `name`, `syntax`, `meaning` and `examples`."""
    # Given a table of entries
    table = TABLE

    # When it is rendered as JSON
    text = render_reference(table, as_json=True)

    # Then the output is one compact array ending in a line ending, with an
    # object for each entry in the table's order, whose four fields equal the
    # entry's in the order name, syntax, meaning and examples
    assert text.endswith("]\n")
    assert ", " in text
    found = loads(text)
    assert [list(item) for item in found] == [
        ["name", "syntax", "meaning", "examples"]
    ] * 3
    assert [
        (item["name"], item["syntax"], item["meaning"], tuple(item["examples"]))
        for item in found
    ] == [(s.name, s.syntax, s.meaning, s.examples) for s in TABLE]


def test_the_real_table_is_printed_whole_and_in_its_order() -> None:
    """AC-1: the entries of `DIRECTIVES` come out unsorted and unfiltered."""
    # Given the table of the directive parser
    # When it is rendered in both forms
    text = render_reference(DIRECTIVES, as_json=False)
    found = loads(render_reference(DIRECTIVES, as_json=True))

    # Then every entry is there once, in the order `required`, `items`, `pattern`,
    # `inherit`, and every field of the table is printed as it is
    names = ["required", "items", "pattern", "inherit"]
    assert [item["name"] for item in found] == names
    assert [line for line in text.splitlines() if line and line[0] != " "] == names
    for spec in DIRECTIVES:
        assert f"  Syntax: {spec.syntax}\n" in text
        assert spec.meaning in text
        assert all(f"  Example: {example}\n" in text for example in spec.examples)


def test_an_empty_table_gives_nothing_or_an_empty_array() -> None:
    """AC-1 and AC-2: no entry is an empty text, or `[]` for JSON."""
    # Given an empty table
    # When it is rendered for a person and as JSON
    human = render_reference((), as_json=False)
    machine = render_reference((), as_json=True)

    # Then the first is empty and the second is an empty array with its ending
    assert (human, machine) == ("", "[]\n")


def test_an_entry_with_no_example_has_no_example_line_and_an_empty_array() -> None:
    """AC-1 and AC-2: the examples are printed as they are, even when none."""
    # Given an entry with no example
    entry = (DirectiveSpec("none", "none", "Nothing.", ()),)

    # When it is rendered in both forms
    human = render_reference(entry, as_json=False)
    machine = loads(render_reference(entry, as_json=True))

    # Then its block has no `Example:` line and its object has an empty array
    assert "Example" not in human
    assert machine[0]["examples"] == []


def test_the_same_table_always_gives_the_same_text() -> None:
    """AC-7: both forms are the same on every call."""
    # Given the table of the directive parser
    # When each form is rendered twice
    first = [render_reference(DIRECTIVES, as_json=flag) for flag in (False, True)]
    second = [render_reference(DIRECTIVES, as_json=flag) for flag in (False, True)]

    # Then the two results of each form are identical
    assert first == second
