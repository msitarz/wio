# SPDX-License-Identifier: Apache-2.0
"""Tests for the glossary of the test setup."""

from pathlib import Path

GLOSSARY = Path(__file__).resolve().parents[2] / "GLOSSARY.md"


def _rows(text: str) -> dict[str, str]:
    """Map each term of the glossary table to its row.

    Args:
        text: The glossary's markdown.

    Returns:
        The rows of the table, keyed by the term in the first column.
    """
    rows = [line for line in text.splitlines() if line.startswith("| ")]
    return {row.split("|")[1].strip(): row for row in rows}


def test_the_glossary_defines_the_terms_of_the_test_setup() -> None:
    """Channel, Test driver, Facade and Sandbox each have a row."""
    # Given the glossary of the tests
    text = GLOSSARY.read_text(encoding="utf-8")

    # When the terms it defines are listed
    terms = set(_rows(text))

    # Then the four terms of the test setup are among them
    assert {"Channel", "Test driver", "Facade", "Sandbox"} <= terms


def test_the_test_driver_entry_says_how_it_narrows_the_driver() -> None:
    """The entry for Test driver names the root Driver and the difference."""
    # Given the glossary of the tests
    text = GLOSSARY.read_text(encoding="utf-8")

    # When the row of Test driver is found
    row = _rows(text)["Test driver"]

    # Then it names the root Driver it narrows and what that one does
    assert "narrows the root glossary's Driver" in row
    assert "advances a Work" in row


def test_the_glossary_binds_itself_to_the_tests() -> None:
    """The introduction says it binds to this directory and its descendants."""
    # Given the glossary of the tests
    text = GLOSSARY.read_text(encoding="utf-8")

    # When its introduction is read
    binds = "bind to this directory and its descendants" in text

    # Then it binds the terms
    assert binds
