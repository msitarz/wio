# SPDX-License-Identifier: Apache-2.0
"""Tests of how the text and the JSON of `show` are composed from their leaves."""

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

from wio.contracts import show_render as module
from wio.contracts.showing import ShownWork
from wio.models.frozen import freeze
from wio.models.works import Work

if TYPE_CHECKING:
    import pytest


def _shown(view: str) -> ShownWork:
    """Build a Work that is shown with a view.

    Args:
        view: The resolved view.

    Returns:
        A Work with nothing else to say.
    """
    work = Work("k3m9xq", "T", Path("a/README.md"), None, (), (), freeze({}))
    return ShownWork(work, None, (), (), (), (), view)


def test_the_text_is_the_facts_the_actions_a_rule_and_the_view_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The first line, the facts, the actions and the view are joined by the layout."""
    # Given leaves that give a first line, two fact lines and one action line
    monkeypatch.setattr(module, "_first_line", Mock(return_value="Work k3m9xq  T"))
    monkeypatch.setattr(
        module, "_fact_lines", Mock(return_value=["  Path  a", "  B  b"])
    )
    monkeypatch.setattr(module, "_action_lines", Mock(return_value=["  none"]))

    # When the text is rendered with a view
    text = module.render_show(_shown("# T\n"), as_json=False)

    # Then a blank line, `Actions`, the actions, a blank line, a rule and a blank
    # line stand between the facts and the view, and the text ends in the view
    assert text == (
        "Work k3m9xq  T\n  Path  a\n  B  b\n\nActions\n  none\n\n----\n\n# T\n"
    )


def test_the_json_is_the_object_of_the_leaf_on_one_line_with_one_line_ending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The JSON is the object that the leaf describes, encoded."""
    # Given a leaf that describes the Work as an object
    described = {"id": "k3m9xq", "title": None, "view": "# T\n"}
    monkeypatch.setattr(module, "_as_object", Mock(return_value=described))

    # When it is rendered as JSON
    text = module.render_show(_shown("# T\n"), as_json=True)

    # Then it is the encoding of the object, in its order, ending in one line
    # ending
    assert text == json.dumps(described) + "\n"
    assert text.count("\n") == 1


def test_an_empty_view_ends_the_text_at_the_rule_with_one_line_ending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Work with no view has no blank line after the rule."""
    # Given leaves that give a first line, no fact and no action line, and a Work
    # whose view is empty
    monkeypatch.setattr(module, "_first_line", Mock(return_value="Work k3m9xq  T"))
    monkeypatch.setattr(module, "_fact_lines", Mock(return_value=[]))
    monkeypatch.setattr(module, "_action_lines", Mock(return_value=["  none"]))

    # When the text is rendered
    text = module.render_show(_shown(""), as_json=False)

    # Then it ends at the rule with exactly one line ending
    assert text == "Work k3m9xq  T\n\nActions\n  none\n\n----\n"
