# SPDX-License-Identifier: Apache-2.0
"""Tests of the resolution of a Work's actions."""

from pathlib import Path

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts.actions import ResolvedAction, resolve_actions, template_actions
from wio.models.template import Template

TEMPLATE = Template("t", "feature", None, None, Path("templates/t.md"), entry=False)


def _read(text: str | None, error: Exception | None = None) -> object:
    """Read the actions of a template whose file holds a text.

    Args:
        text: The file's text, or `None` for no file.
        error: A failure that reading the file raises, instead of its text.

    Returns:
        What `template_actions` gave.
    """
    path = ROOT / TEMPLATE.path
    disk = MemoryFileSystem({path: text} if text is not None else {})
    if error is not None:
        disk.broken[path] = error
    return template_actions(TEMPLATE, ROOT, disk)


def test_a_layering_replaces_an_inherited_action_and_keeps_its_source() -> None:
    """The Work's own action replaces the inherited one, and the rest stays."""
    # Given a template with two actions and a Work that overrides the first
    inherited = {"define": "define-feature", "deliver": ("a", "b")}
    own = {"deliver": ("c",)}

    # When they are resolved
    found = resolve_actions(own, inherited, "template")

    # Then the Work's wins with its own source, and the other keeps the template's
    assert found == (
        ResolvedAction("define", "define-feature", "template", removed=False),
        ResolvedAction("deliver", ("c",), "work", removed=False),
    )


def test_the_defaults_apply_only_to_a_work_without_a_template() -> None:
    """What the caller says is inherited is what is layered, and it names its source."""
    # Given the config defaults and a Work that adds an action
    defaults = {"deliver": ("a",)}
    own = {"amend": ("b",)}

    # When they are resolved as the defaults
    found = resolve_actions(own, defaults, "defaults")

    # Then the defaults come first with their source, and the Work's after them
    assert [(e.name, e.source) for e in found] == [
        ("deliver", "defaults"),
        ("amend", "work"),
    ]


def test_an_empty_inherited_list_is_the_same_as_leaving_the_action_out() -> None:
    """A template or a default that empties an action gives no entry."""
    # Given inherited actions of which one is an empty list
    inherited = {"define": (), "deliver": ("a",)}

    # When they are resolved with no action of the Work's own
    found = resolve_actions({}, inherited, "defaults")

    # Then only the other action is there
    assert [e.name for e in found] == ["deliver"]


def test_an_empty_list_that_nothing_inherited_gives_no_entry() -> None:
    """Only an inherited action can be removed."""
    # Given a Work that empties an action its template does not have, and one
    # that empties an action that it has
    inherited = {"deliver": ("a",)}

    # When they are resolved
    nothing = resolve_actions({"amend": ()}, inherited, "template")
    removed = resolve_actions({"deliver": ()}, inherited, "template")

    # Then the first gives no entry for it and the second a removed entry
    assert [e.name for e in nothing] == ["deliver"]
    assert removed == (ResolvedAction("deliver", (), "work", removed=True),)


def test_an_overridden_action_keeps_the_place_of_the_one_it_replaces() -> None:
    """The order is the inherited actions, then the Work's own new ones."""
    # Given a template with two actions and a Work that overrides the first and
    # adds a third
    inherited = {"first": ("a",), "second": ("b",)}
    own = {"third": ("c",), "first": ("d",)}

    # When they are resolved
    found = resolve_actions(own, inherited, "template")

    # Then the first is overridden in place, the second follows and the third is last
    assert [(e.name, e.source) for e in found] == [
        ("first", "work"),
        ("second", "template"),
        ("third", "work"),
    ]


def test_the_actions_of_a_template_are_read_from_its_file() -> None:
    """The actions are in the order written, empty for none."""
    # Given templates with actions, with an empty table and with no table
    with_actions = '<!-- wio\n\n[actions]\nb = "p"\na = ["x", "y"]\n-->\n'
    empty_table = "<!-- wio\n\n[actions]\n-->\n"
    none = '<!-- wio\nkind = "feature"\n-->\n'

    # When the actions are read
    found = [_read(with_actions), _read(empty_table), _read(none)]

    # Then the first gives them in order, the others give none
    assert found[0] == {"b": "p", "a": ("x", "y")}
    assert list(found[0]) == ["b", "a"]  # type: ignore[call-overload]
    assert found[1:] == [{}, {}]


def test_a_template_whose_actions_are_not_a_table_of_pipelines_gives_none() -> None:
    """A-4: a template that cannot be read for its actions is skipped."""
    # Given a template whose `[actions]` hold a number, one whose block does not
    # close, one with no block, one that cannot be read, one that is not text,
    # and one that does not exist
    number = "<!-- wio\n\n[actions]\ndeliver = 3\n-->\n"
    unclosed = '<!-- wio\nkind = "feature"\n'
    no_block = "# A template without a block\n"
    unreadable = _read("<!-- wio\n-->\n", OSError(5, "I/O error"))
    not_text = _read("", UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad byte"))
    missing = _read(None)

    # When the actions are read
    found = [_read(number), _read(unclosed), _read(no_block)]

    # Then each answer is `None`
    assert found == [None, None, None]
    assert (unreadable, not_text, missing) == (None, None, None)
