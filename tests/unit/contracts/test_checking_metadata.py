# SPDX-License-Identifier: Apache-2.0
"""Tests of the checks of the metadata of a Work: its keys and its id."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.unit.contracts.helpers import work_with_id
from wio.contracts import checking as module
from wio.contracts.discovery import wrong_optional_fields
from wio.formats import read_metadata_block

if TYPE_CHECKING:
    from wio.models.block import MetadataBlock
    from wio.models.works import Work


def _block(lines: str) -> MetadataBlock:
    """Read a block of a file.

    Args:
        lines: The lines of the block.

    Returns:
        The block.
    """
    block = read_metadata_block(f'<!-- wio\nid = "a1"\n{lines}\n-->\n\n# Title\n')
    assert block is not None
    return block


def _messages(lines: str) -> list[tuple[str, str]]:
    """List the warnings that the keys of a block give.

    Args:
        lines: The lines of the block after the `id`.

    Returns:
        The severity and the message of each.
    """
    work = work_with_id("a1")
    found = module._key_warnings(work, _block(lines))  # noqa: SLF001
    assert {d.where for d in found} <= {work.path.as_posix()}
    return [(d.severity, d.message) for d in found]


def test_an_unknown_key_is_a_warning_with_its_closest_known_key() -> None:
    """The suggestion is the closest of the keys that wio reads."""
    # Given a block with a mistyped key and one that is far from any
    lines = "depend_on = []\nzzz = 1"

    # When its keys are checked
    found = _messages(lines)

    # Then the first names the closest key and the second suggests none
    assert found == [
        (
            "warning",
            "Unknown key `depend_on` in the metadata. Did you mean `depends_on`?",
        ),
        ("warning", "Unknown key `zzz` in the metadata"),
    ]


def test_a_plain_x_and_an_unknown_table_are_unknown_and_never_suggested() -> None:
    """Only the table `x` and the key `tracks` are left alone."""
    # Given a plain `x`, the table `[xx]`, and in other blocks the table `[x]`
    # and the key `tracks`
    unknown = _messages("x = 1\n\n[xx]\nk = 1")
    exempt = [_messages("tracks = 1"), _messages("[x]\nk = 1")]

    # When their keys are checked
    # Then the first two are warned of without a suggestion, and the others are not
    assert unknown == [
        ("warning", "Unknown key `x` in the metadata"),
        ("warning", "Unknown key `xx` in the metadata"),
    ]
    assert exempt == [[], []]


def test_the_known_keys_and_the_marker_give_no_warning() -> None:
    """The keys that wio reads are not unknown, and the marker is not a key."""
    # Given a block with every known key
    lines = 'template = "t"\nroots = []\ndepends_on = []\n\n[actions]\ndeliver = "p"'

    # When its keys are checked
    found = _messages(lines)

    # Then there is no warning
    assert found == []


@pytest.mark.parametrize(
    ("work_id", "message"),
    [
        ("a b", "The id `a b` holds whitespace or a comma"),
        ("a,b", "The id `a,b` holds whitespace or a comma"),
        ("a\tb", "The id `a\tb` holds whitespace or a comma"),
        ("none", "The id `none` is reserved for commits that belong to no Work"),
    ],
)
def test_an_id_that_would_break_a_record_is_an_error(
    work_id: str, message: str
) -> None:
    """A space, a comma and `none` are refused."""
    # Given a Work with the id
    work = work_with_id(work_id)

    # When its id is checked
    found = module._id_error(work)  # noqa: SLF001

    # Then it is one error at the Work's file
    assert [(d.severity, d.where, d.message) for d in found] == [
        ("error", work.path.as_posix(), message)
    ]


@pytest.mark.parametrize(
    "work_id", ["SPEC-012", "k3m9xq", "None", "a_b", "nonexistent"]
)
def test_any_other_id_is_accepted(work_id: str) -> None:
    """Only whitespace, a comma and exactly `none` are refused."""
    # Given a Work with the id
    work: Work = work_with_id(work_id)

    # When its id is checked
    found = module._id_error(work)  # noqa: SLF001

    # Then there is no error
    assert found == []
    assert Path(work.path).name == "README.md"


def test_discovery_and_the_check_agree_on_which_fields_are_of_a_wrong_type() -> None:
    """A field that discovery reports is one that the check does not resolve."""
    # Given blocks with a wrong `template`, `roots`, `depends_on` and `[actions]`
    # and one with every field right
    wrong = _block(
        'template = 1\nroots = "a"\ndepends_on = [1]\n\n[actions]\ndeliver = 3'
    )
    right = _block(
        'template = "t"\nroots = ["a"]\ndepends_on = []\n\n[actions]\nd = ["s"]'
    )

    # When the fields are type-tested
    # Then all four are wrong in the first and none in the second
    assert wrong_optional_fields(wrong.data) == {
        "template",
        "roots",
        "depends_on",
        "actions",
    }
    assert wrong_optional_fields(right.data) == frozenset()
