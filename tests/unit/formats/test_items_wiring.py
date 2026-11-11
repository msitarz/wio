# SPDX-License-Identifier: Apache-2.0
"""Tests of how the items of a section are composed from their leaves."""

from typing import TYPE_CHECKING
from unittest.mock import Mock

from wio.formats import items as module
from wio.models.diagnostics import Diagnostic
from wio.models.heading import Heading
from wio.models.item import Item, SectionItems

if TYPE_CHECKING:
    import pytest

SECTION = Heading(2, "Goals", "## Goals", 1)


def test_the_items_come_from_the_outline_of_the_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The finder reads the outline of the body and hands it to its leaf."""
    # Given a leaf that finds one item
    item = Item("Goals", "X", 5)
    leaf = Mock(return_value=(item,))
    monkeypatch.setattr(module, "_items_of", leaf)

    # When the items of a section are found in a body that starts on line 5
    found = module.find_items("## Goals\n", 5, SECTION, ())

    # Then the leaf got the outline of that body and gave the item back
    assert found == (item,)
    assert leaf.call_args.args[2] == (Heading(2, "Goals", "## Goals", 5),)


def test_the_findings_come_back_in_the_order_of_sort_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The judge sorts what its leaf reports, by place as a string."""
    # Given a leaf that reports errors out of order
    places = ("c.md:2", "c.md:10", "c.md:1")
    leaf = Mock(return_value=iter(Diagnostic("error", p, "m") for p in places))
    monkeypatch.setattr(module, "_findings", leaf)

    # When the items are judged
    found = module.judge_items("c.md", [SectionItems(SECTION, (), ())])

    # Then they come back by place, as strings, so line 10 comes before line 2
    assert [finding.where for finding in found] == [
        "c.md:1",
        "c.md:10",
        "c.md:2",
    ]
