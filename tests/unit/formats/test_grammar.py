# SPDX-License-Identifier: Apache-2.0
"""Tests of the grammar of a reference and the forms of the names in it."""

from typing import TYPE_CHECKING

import pytest

from wio.formats import grammar
from wio.formats.grammar import Bare, Malformed, Qualified

if TYPE_CHECKING:
    import re

_STUB = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="stub")


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("mine", grammar.Bare("mine")),
        ("define-bugfix", grammar.Bare("define-bugfix")),
        ("docs.DOC", grammar.Qualified("docs", "DOC")),
        ("docs.DOC001", grammar.Qualified("docs", "DOC001")),
        ("docs.all", grammar.Qualified("docs", "all")),
        ("DOC", "is not a rule preset name"),
        ("Docs.DOC", "the ruleset part `Docs`"),
        ("docs.Doc1", "the item `Doc1`"),
        ("docs.DOC001.x", "has more than one dot"),
        ("docs.", "the item ``"),
        (".DOC", "the ruleset part ``"),
    ],
)
def test_a_reference_has_the_form_of_its_kind(
    text: str, kind: grammar.Reference | str
) -> None:
    """AC-2: a bare name, a ruleset name and the parts of a qualified reference."""
    # Given a reference as the config writes it

    # When its form is judged
    found = grammar.parse_reference(text)

    # Then a bare name and a qualified reference with parts in their forms are
    # told apart, and any other text says which part is wrong and the form it
    # should have
    if isinstance(kind, str):
        assert isinstance(found, grammar.Malformed)
        assert kind in found.message
        assert grammar.NAME_FORM in found.message or "bare name or" in found.message
    else:
        assert found == kind


def test_a_reference_of_the_config_is_bare_qualified_or_malformed() -> None:
    """AC-2: a rule preset name, `<ruleset>.<item>` and a bare upper-case name."""
    # Given the texts `recommended`, `demo.ARC` and `ARC001`
    texts = ["recommended", "demo.ARC", "ARC001"]

    # When each is read as a reference of the config
    found = [grammar.parse_reference(text) for text in texts]

    # Then the first is bare, the second qualified, and the third malformed
    assert found[0] == Bare("recommended")
    assert found[1] == Qualified("demo", "ARC")
    assert isinstance(found[2], Malformed)


@_STUB
def test_an_entry_of_a_manifest_is_read_as_its_own_item() -> None:
    """AC-3: a family, a code and a rule preset name are bare, `Docs` is not."""
    # Given the texts `ARC`, `ARC001`, `local`, `demo.ARC` and `Docs`
    texts = ["ARC", "ARC001", "local", "demo.ARC", "Docs"]

    # When each is read as an entry of a manifest
    found = [grammar.parse_own_item(text) for text in texts]

    # Then the first three are bare, the fourth is qualified, and `Docs` is
    # malformed
    assert found[:3] == [Bare("ARC"), Bare("ARC001"), Bare("local")]
    assert found[3] == Qualified("demo", "ARC")
    assert isinstance(found[4], Malformed)


@pytest.mark.parametrize(
    ("form", "accepted", "rejected"),
    [
        (grammar.NAME, ("demo", "my-rules_2"), ("My_Rules", "2x")),
        (grammar.FAMILY, ("ARC",), ("Arc",)),
        (grammar.CODE, ("ARC001", "A1"), ("arc001", "ARC")),
    ],
)
def test_the_name_forms_accept_and_reject(
    form: re.Pattern[str], accepted: tuple[str, ...], rejected: tuple[str, ...]
) -> None:
    """AC-4: the forms of a ruleset name, a family and a code."""
    # Given a form, and names that have it and names that do not

    # When each name is matched against the form
    matched = [name for name in (*accepted, *rejected) if form.fullmatch(name)]

    # Then exactly the names that have the form match
    assert matched == list(accepted)


@pytest.mark.parametrize(
    ("item", "kind"),
    [
        ("ARC", "family"),
        ("ARC001", "code"),
        ("recommended", "rule preset"),
        ("arc001", "rule preset"),
        ("Docs", None),
    ],
)
def test_a_name_is_told_apart_by_its_form(item: str, kind: str | None) -> None:
    """AC-5: a family, a code, a rule preset name or none."""
    # Given an item written after the dot

    # When its kind is told
    found = grammar.item_kind(item)

    # Then it is the kind its form has, or none
    assert found == kind
