# SPDX-License-Identifier: Apache-2.0
"""Tests for what `tests/README.md` says about the channels and test drivers."""

import re
from pathlib import Path

README = Path(__file__).resolve().parents[2] / "README.md"


def _text() -> str:
    """Read the test strategy with its line breaks collapsed.

    Returns:
        The document's text, each run of whitespace as one space.
    """
    return " ".join(README.read_text(encoding="utf-8").split())


def test_the_readme_gives_each_channel_its_role() -> None:
    """The CLI channel is the reference, the in-process one the fast copy."""
    # Given the test strategy
    text = _text()

    # When its statements about the channels are looked for
    reference = "The CLI channel is the reference for acceptance" in text
    fast_copy = "in-process channel is the fast copy of the same scenarios" in text
    layered = "layered on the test driver's `run(args)` as scenarios need them" in text

    # Then the roles and the note on layered verbs are there
    assert (reference, fast_copy, layered) == (True, True, True)


def test_the_readme_does_not_make_the_cli_channel_opt_in() -> None:
    """Neither the opt-in sentence nor the restriction to CLI wiring is left."""
    # Given the test strategy
    text = _text()

    # When the old statements are looked for
    old = ("opt-in per test" in text, "only where the CLI wiring matters" in text)

    # Then neither is there
    assert old == (False, False)


def test_the_layout_and_order_name_the_first_scenario() -> None:
    """The layout lists `tests/acceptance/cli/` and step 2 names bare `wio`."""
    # Given the test strategy
    text = README.read_text(encoding="utf-8")

    # When the layout and step 2 are looked for
    layout = "│   ├── cli/" in text
    step = re.search(r"^2\. .*?(?=^3\.)", text, re.DOTALL | re.MULTILINE)

    # Then the layout lists the folder and the step names the scenario
    assert layout
    assert step is not None
    assert "bare `wio` scenario" in " ".join(step.group(0).split())


def test_the_readme_says_test_driver_everywhere() -> None:
    """The word driver always follows `test`, outside identifiers and paths."""
    # Given the test strategy
    text = _text()

    # When each use of the word that is not part of an identifier or path is found
    bare = re.findall(r"(?<![\w/`])(?<!test )drivers?\b(?!/)", text, re.IGNORECASE)

    # Then none stands alone
    assert bare == []
