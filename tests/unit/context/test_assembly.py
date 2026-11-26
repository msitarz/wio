# SPDX-License-Identifier: Apache-2.0
"""Check the text and identity of an assembled bundle.

Each case exercises assembly with a supplied header builder and rendered parts.
"""

from unittest.mock import Mock

import pytest

from wio.context.assembly import assemble
from wio.context.identity import bundle_id

_CLOSING = "If your context was compacted, run the command in the header again.\n"
_HEADER = "HEADER 1\nHEADER 2"
_BODY = (
    "--- stage ---\n\nGOAL\n\n"
    "--- contract ---\n\nCONTRACT\n\n"
    "--- rules ---\n\nRULES\n\n"
    f"{_CLOSING}"
)


def test_bundle_sections_and_parts_come_in_order() -> None:
    """Keep the exact layout and id of a bundle with all its parts.

    The metadata, header and body have fixed blank-line boundaries.
    """
    # Given guidance, a contract and rules for a stage
    header_for = Mock(return_value=_HEADER)

    # When the bundle is assembled
    bundle = assemble("GOAL", "CONTRACT", "RULES", header_for)

    # Then every section and labelled part comes in order
    assert bundle == f"bundle: 7a2383bc4098\n\n{_HEADER}\n\n{_BODY}"


@pytest.mark.parametrize(("goal", "size"), [("GOAL", 139), ("GÓAL", 140)])
def test_header_measures_the_body_and_id_names_the_text_after_metadata(
    goal: str, size: int
) -> None:
    """Keep header length out of body size and include the header in the id.

    Args:
        goal: The stage guidance with ASCII or multibyte text.
        size: The body's expected UTF-8 byte count.
    """
    # Given the same parts and headers of different lengths
    short_header = Mock(return_value="HEADER")
    long_header = Mock(return_value="HEADER\nWORK\nCOMMAND")

    # When each bundle is assembled
    short_bundle = assemble(goal, "CONTRACT", "RULES", short_header)
    long_bundle = assemble(goal, "CONTRACT", "RULES", long_header)

    # Then the measured body is the same and each id names its own text
    short_header.assert_called_once_with(size, 13)
    long_header.assert_called_once_with(size, 13)
    for bundle in (short_bundle, long_bundle):
        metadata, _, text = bundle.partition("\n\n")
        assert metadata == f"bundle: {bundle_id(text)}"


def test_assembly_removes_only_trailing_newlines() -> None:
    """Preserve the whitespace within parts and end the bundle once.

    A part's final newlines leave the same spacing as a part without them.
    """
    # Given guidance with leading and trailing whitespace and a contract
    # with two trailing newlines
    header_for = Mock(return_value=_HEADER)

    # When the bundle is assembled with those parts and rules
    bundle = assemble("\n GOAL ", "CONTRACT\n\n", "RULES", header_for)
    _, _, text = bundle.partition("\n\n")

    # Then the guidance keeps its whitespace and the closing line ends once
    assert text == f"{_HEADER}\n\n" + _BODY.replace("GOAL", "\n GOAL ")


@pytest.mark.parametrize(
    ("stage", "contract", "rules", "parts"),
    [
        ("GOAL", "", "\n\n", "--- stage ---\n\nGOAL\n\n"),
        (
            "",
            "CONTRACT",
            "RULES",
            "--- contract ---\n\nCONTRACT\n\n--- rules ---\n\nRULES\n\n",
        ),
        ("", "", "", ""),
        (" ", "", "", "--- stage ---\n\n \n\n"),
    ],
)
def test_empty_parts_leave_no_label(
    stage: str, contract: str, rules: str, parts: str
) -> None:
    """Omit empty parts and keep the text of the parts that remain.

    Args:
        stage: The rendered stage guidance.
        contract: The rendered contract.
        rules: The rendered rules.
        parts: The expected labelled parts before the closing line.
    """
    # Given the selected parts and a fixed header
    header_for = Mock(return_value=_HEADER)
    text = f"{_HEADER}\n\n{parts}{_CLOSING}"

    # When the bundle is assembled
    bundle = assemble(stage, contract, rules, header_for)

    # Then empty parts leave no labels and the id names the remaining text
    assert bundle == f"bundle: {bundle_id(text)}\n\n{text}"
