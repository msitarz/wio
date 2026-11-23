# SPDX-License-Identifier: Apache-2.0
"""Tests of the key paths and the lists of names that messages write."""

import pytest

from wio.formats import wording


@pytest.mark.parametrize(
    ("parent", "key", "path"),
    [
        ("", "description", "description"),
        ("rule_presets", "x", "rule_presets.x"),
        ("families", "a.b", 'families."a.b"'),
    ],
)
def test_a_key_is_added_to_a_key_path_and_quoted_when_it_needs_it(
    parent: str, key: str, path: str
) -> None:
    """AC-6: a key of letters, digits, `_` and `-` is bare, any other is quoted."""
    # Given a key path and a key to add

    # When the key is added
    found = wording.join_path(parent, key)

    # Then the path is longer by the key, in quotes when TOML needs them
    assert found == path


def test_an_index_is_added_to_a_key_path() -> None:
    """AC-6: the path of an item of a list."""
    # Given the list `rules_include` and the index 0

    # When the index is added
    found = wording.item_path("rules_include", 0)

    # Then the path is `rules_include[0]`
    assert found == "rules_include[0]"


def test_names_are_quoted_and_a_declared_list_says_when_it_is_empty() -> None:
    """AC-7: names in backticks, what is declared, and that nothing is."""
    # Given the names `ARC` and `PAY`, and none
    names = ["ARC", "PAY"]

    # When they are quoted and listed as declared
    quoted = wording.quoted(names)
    some = wording.declared("Declared families", "No families are declared.", names)
    none = wording.declared("Declared families", "No families are declared.", [])

    # Then the names are in backticks, and an empty list gives the sentence
    assert quoted == "`ARC`, `PAY`"
    assert some == "Declared families: `ARC`, `PAY`."
    assert none == "No families are declared."


@pytest.mark.parametrize(
    ("items", "text"),
    [(["a"], "a"), (["a", "b"], "a and b"), (["a", "b", "c"], "a, b and c")],
)
def test_items_are_joined_as_english_does(items: list[str], text: str) -> None:
    """AC-7: one, two and three or more items."""
    # Given some items

    # When they are joined
    found = wording.and_list(items)

    # Then they read as English does
    assert found == text
