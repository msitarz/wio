# SPDX-License-Identifier: Apache-2.0
"""Tests of the words the shape uses for what a file holds and what a key takes."""

import datetime

import pytest

from wio.config import messages
from wio.config.schema import Atom, Open, Spec, Strings, Table


@pytest.mark.parametrize(
    ("value", "shown"),
    [
        (True, "true"),
        (False, "false"),
        ("flat", '"flat"'),
        ('a "b"', '"a \\"b\\""'),
        (3, "3"),
        (1.5, "1.5"),
        ([1, 2], "a list"),
        ({"a": 1}, "a table"),
        (datetime.date(2026, 1, 2), "date"),
    ],
)
def test_a_received_value_is_shown_as_toml_writes_it_or_by_its_kind(
    value: object, shown: str
) -> None:
    """AC-4: a scalar is shown as written, and the rest by what it is."""
    # Given a value that a file holds

    # When it is shown in a message
    text = messages.show(value)

    # Then a scalar is as TOML writes it, a collection is a list or a table, and
    # anything else is named by its type
    assert text == shown


@pytest.mark.parametrize(
    ("spec", "phrase"),
    [
        (Atom(str), "a string"),
        (Atom(bool), "a boolean"),
        (Atom(int), "an integer"),
        (Strings(), "a list of strings"),
        (Table(dict, "a stage", ()), "a table (a stage)"),
        (Open(Atom(str)), "a table"),
    ],
)
def test_what_a_key_takes_is_said_in_one_phrase(spec: Spec, phrase: str) -> None:
    """AC-4: the expected kind of a value is a short phrase a person can act on."""
    # Given what a key takes

    # When the expected kind is worded
    text = messages.expected(spec)

    # Then it is the phrase for that kind
    assert text == phrase
