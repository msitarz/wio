# SPDX-License-Identifier: Apache-2.0
"""Tests of the rendering of `wio templates list` in `wio.templates`."""

from json import loads
from pathlib import Path

from wio.models.template import Template
from wio.templates.listing import render_list

DIR = Path(".agents/wio/templates")


def _template(
    name: str,
    kind: str,
    *,
    shape: str | None = None,
    description: str | None = None,
    entry: bool = False,
) -> Template:
    """Make a template in the default directory.

    Args:
        name: The template's name.
        kind: Its kind.
        shape: Its shape, if any.
        description: Its description, if any.
        entry: Whether it is the entry of its kind.

    Returns:
        The template.
    """
    return Template(name, kind, shape, description, DIR / f"{name}.md", entry)


PROJECT = [
    _template(
        "feature.leaf",
        "feature",
        shape="leaf",
        description="A capability\ndelivered as one outcome.",
    ),
    _template(
        "feature.draft",
        "feature",
        shape="draft",
        description="The working space of a new Work.",
        entry=True,
    ),
    _template("old.note", "old"),
    _template("bugfix.fix", "bugfix", entry=True),
]


def test_the_human_form_groups_by_kind_and_aligns_the_columns() -> None:
    """AC-5: kinds in order, the entry marked, names padded, descriptions kept."""
    # Given templates of three kinds, in no order, with and without a shape and a
    # description, and one entry mark in two of the groups
    templates = PROJECT

    # When they are rendered for a person
    text = render_list(templates, as_json=False)

    # Then the lines are exactly those of the contract, without trailing spaces
    assert text == (
        "bugfix\n"
        "  bugfix.fix [entry]\n"
        "\n"
        "feature\n"
        "  feature.draft [entry] shape: draft\n"
        "    The working space of a new Work.\n"
        "  feature.leaf          shape: leaf\n"
        "    A capability\n"
        "    delivered as one outcome.\n"
        "\n"
        "old\n"
        "  old.note\n"
    )


def test_a_description_is_printed_as_written_with_its_outer_empty_lines_dropped() -> (
    None
):
    """AC-5: each line of a description is kept, and the empty lines around it go."""
    # Given a template whose description has an indented line, an empty line in
    # the middle, and empty lines around it
    description = "\n\nFirst\n  indented\n\nlast\n\n"
    templates = [_template("a", "k", description=description)]

    # When it is rendered for a person
    text = render_list(templates, as_json=False)

    # Then every line is indented under the name as written, the inner empty line
    # stays empty and the outer ones are dropped
    assert text == "k\n  a\n    First\n      indented\n\n    last\n"


def test_no_templates_render_as_nothing_or_an_empty_array() -> None:
    """AC-5: no templates give an empty text, or `[]` as JSON."""
    # Given no templates
    # When they are rendered for a person and as JSON
    human = render_list([], as_json=False)
    machine = render_list([], as_json=True)

    # Then the first is empty and the second is an empty array
    assert (human, machine) == ("", "[]\n")


def test_the_json_form_is_one_sorted_array_of_objects() -> None:
    """AC-5: objects with the fields of the contract, sorted by kind and name."""
    # Given templates of three kinds, in no order, some without a shape and a
    # description
    templates = PROJECT

    # When they are rendered as JSON
    found = loads(render_list(templates, as_json=True))

    # Then they are sorted by kind and name, with `null` for the missing fields
    # and the path written with `/`
    assert [(item["kind"], item["name"]) for item in found] == [
        ("bugfix", "bugfix.fix"),
        ("feature", "feature.draft"),
        ("feature", "feature.leaf"),
        ("old", "old.note"),
    ]
    assert found[0] == {
        "name": "bugfix.fix",
        "kind": "bugfix",
        "shape": None,
        "entry": True,
        "description": None,
        "path": ".agents/wio/templates/bugfix.fix.md",
    }
    assert list(found[1]) == [
        "name",
        "kind",
        "shape",
        "entry",
        "description",
        "path",
    ]


def test_the_mark_column_is_present_only_in_a_group_with_an_entry() -> None:
    """AC-5: a group with no entry has no gap where the mark would be."""
    # Given a group with no entry template whose templates have shapes, and a
    # group that has one entry and one template without a mark
    templates = [
        _template("a.draft", "a", shape="draft"),
        _template("a.leaf", "a", shape="leaf"),
        _template("b.draft", "b", shape="draft", entry=True),
        _template("b.leaf", "b", shape="leaf"),
    ]

    # When they are rendered for a person
    text = render_list(templates, as_json=False)

    # Then the first group has a single space before each shape, and the second
    # keeps the width of the mark
    assert text == (
        "a\n"
        "  a.draft shape: draft\n"
        "  a.leaf  shape: leaf\n"
        "\n"
        "b\n"
        "  b.draft [entry] shape: draft\n"
        "  b.leaf          shape: leaf\n"
    )


def test_templates_are_sorted_by_kind_and_then_by_name() -> None:
    """AC-5: the kind comes first, whatever the names are."""
    # Given a template of kind `b` whose name sorts first, and one of kind `a`
    templates = [_template("a.x", "b"), _template("z.x", "a")]

    # When they are rendered as JSON and for a person
    machine = loads(render_list(templates, as_json=True))
    human = render_list(templates, as_json=False)

    # Then the kind `a` is first in both
    assert [item["name"] for item in machine] == ["z.x", "a.x"]
    assert human == "a\n  z.x\n\nb\n  a.x\n"
