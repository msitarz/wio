# SPDX-License-Identifier: Apache-2.0
"""Tests of the rendering of `wio templates directives` in `wio.templates`."""

from json import loads

from wio.formats.directives import COMBINING, DIRECTIVES
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
RULE = (DirectiveSpec("both", "a, b", "Together.", ("## C <!-- wio: a, b -->",)),)


def _is_printed(spec: DirectiveSpec, text: str) -> bool:
    """Tell whether an entry's fields are in the listing as they are.

    Args:
        spec: The entry.
        text: The human form.

    Returns:
        Whether its syntax, its meaning and each of its examples are there.
    """
    lines = text.splitlines()
    return (
        f"  Syntax: {spec.syntax}" in lines
        and spec.meaning in text
        and all(f"  Example: {example}" in lines for example in spec.examples)
    )


def test_the_human_form_prints_the_directives_and_then_how_they_combine() -> None:
    """AC-1: two sections with a header each, and a block for each entry."""
    # Given a table of entries, one with a meaning of three lines, an empty one
    # between them, one with two examples and one with none, and an entry for
    # combining
    # When it is rendered for a person
    text = render_reference(TABLE, RULE, as_json=False)

    # Then a `directives:` section holds a block for each entry, a `combining:`
    # section follows with its block, one empty line separates blocks and
    # sections, and none follows the last
    assert text == (
        "directives:\n"
        "\n"
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
        "\n"
        "combining:\n"
        "\n"
        "both\n"
        "  Syntax: a, b\n"
        "  Together.\n"
        "  Example: ## C <!-- wio: a, b -->\n"
    )


def test_the_json_form_is_one_object_with_the_two_sections_in_order() -> None:
    """AC-2: the keys `directives` and `combining`, each an array of entries."""
    # Given a table of entries and an entry for combining
    # When it is rendered as JSON
    text = render_reference(TABLE, RULE, as_json=True)

    # Then the output is one compact object ending in a line ending, with the two
    # keys in order, each an array of objects whose four fields equal the entry's
    assert text.endswith("}\n")
    assert ", " in text
    found = loads(text)
    assert list(found) == ["directives", "combining"]
    assert [list(item) for item in found["directives"]] == [
        ["name", "syntax", "meaning", "examples"]
    ] * 3
    for key, specs in (("directives", TABLE), ("combining", RULE)):
        assert [
            (i["name"], i["syntax"], i["meaning"], tuple(i["examples"]))
            for i in found[key]
        ] == [(s.name, s.syntax, s.meaning, s.examples) for s in specs]
    assert len(found["combining"]) == 1


def test_the_real_entries_are_printed_whole_and_in_their_order() -> None:
    """AC-1: `DIRECTIVES` and `COMBINING` come out unsorted and unfiltered."""
    # Given the table of the directive parser and its entry for combining
    # When they are rendered in both forms
    text = render_reference(DIRECTIVES, COMBINING, as_json=False)
    found = loads(render_reference(DIRECTIVES, COMBINING, as_json=True))

    # Then every entry is there once, in the order `required`, `items`, `pattern`,
    # `inherit` and then `several directives`, and every field is printed as it is
    names = ["required", "items", "pattern", "inherit"]
    assert [item["name"] for item in found["directives"]] == names
    assert [item["name"] for item in found["combining"]] == ["several directives"]
    assert [line for line in text.splitlines() if line and line[0] != " "] == [
        "directives:",
        *names,
        "combining:",
        "several directives",
    ]
    assert all(_is_printed(spec, text) for spec in (*DIRECTIVES, *COMBINING))


def test_empty_sections_are_left_out_of_the_text_and_kept_in_the_json() -> None:
    """AC-1 and AC-2: no entry gives no section, and empty arrays in the object."""
    # Given no entries, and only an entry for combining
    # When they are rendered for a person and as JSON
    nothing = render_reference((), (), as_json=False)
    only = render_reference((), RULE, as_json=False)
    machine = render_reference((), (), as_json=True)

    # Then the first is empty, the second has only the `combining:` section, and
    # the object keeps both keys with empty arrays
    assert nothing == ""
    assert only.startswith("combining:\n\nboth\n")
    assert machine == '{"directives": [], "combining": []}\n'


def test_an_entry_with_no_example_has_no_example_line_and_an_empty_array() -> None:
    """AC-1 and AC-2: the examples are printed as they are, even when none."""
    # Given an entry with no example
    entry = (DirectiveSpec("none", "none", "Nothing.", ()),)

    # When it is rendered in both forms
    human = render_reference(entry, (), as_json=False)
    machine = loads(render_reference(entry, (), as_json=True))

    # Then its block has no `Example:` line and its object has an empty array
    assert "Example" not in human
    assert machine["directives"][0]["examples"] == []


def test_the_same_entries_always_give_the_same_text() -> None:
    """AC-7: both forms are the same on every call."""
    # Given the table of the directive parser and its entry for combining
    # When each form is rendered twice
    first = [render_reference(DIRECTIVES, COMBINING, as_json=f) for f in (False, True)]
    second = [render_reference(DIRECTIVES, COMBINING, as_json=f) for f in (False, True)]

    # Then the two results of each form are identical
    assert first == second


def test_a_meaning_is_printed_character_for_character_but_for_its_indent() -> None:
    """AC-1: spaces inside a line of a meaning stay, and an empty line stays empty."""
    # Given an entry whose meaning has a line with leading and trailing spaces and
    # an empty line
    entry = (DirectiveSpec("x", "x", "  kept  \n\nlast", ()),)

    # When it is rendered for a person
    text = render_reference(entry, (), as_json=False)

    # Then the line keeps its spaces after the indent, and the empty line is empty
    assert text == "directives:\n\nx\n  Syntax: x\n    kept  \n\n  last\n"
