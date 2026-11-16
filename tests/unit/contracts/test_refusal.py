# SPDX-License-Identifier: Apache-2.0
"""Tests of how the commands that read the tree refuse."""

import pytest

from tests.unit.fakes import ROOT, MemoryFileSystem
from wio.contracts.discovery import discover_works
from wio.contracts.errors import ContractsError
from wio.contracts.refusal import HINT, refuse_tree
from wio.models.config import Works

BASE = ROOT / ".agents/wio/works"


def _marked(block: str) -> str:
    """Write a file with a metadata block.

    Args:
        block: The lines of the block.

    Returns:
        The text of the file.
    """
    return f"<!-- wio\n{block}\n-->\n\n# Title\n"


def test_a_work_left_out_refuses_the_tree_whether_or_not_shared_ids_do() -> None:
    """An incomplete tree is refused with its errors and the hint."""
    # Given a tree with a Work left out
    files = MemoryFileSystem(
        {
            BASE / "a/README.md": _marked('id = "k3m9xq"'),
            BASE / "b/README.md": _marked(""),
        }
    )
    discovery = discover_works(ROOT, Works(), files)

    # When it is judged with and without shared ids
    for shared in (True, False):
        with pytest.raises(ContractsError) as raised:
            refuse_tree(discovery, shared=shared)

        # Then the errors of discovery are carried, then the hint
        message = str(raised.value)
        assert message.endswith(HINT)
        assert "b/README.md" in message


def test_a_shared_id_refuses_the_tree_only_when_asked() -> None:
    """A command that looks a Work up leaves the shared ids to its lookup."""
    # Given a tree with two Works that share an id
    files = MemoryFileSystem(
        {
            BASE / "a/README.md": _marked('id = "a7b2c4"'),
            BASE / "b/README.md": _marked('id = "a7b2c4"'),
        }
    )
    discovery = discover_works(ROOT, Works(), files)

    # When it is judged without and with shared ids
    refuse_tree(discovery, shared=False)
    with pytest.raises(ContractsError) as raised:
        refuse_tree(discovery, shared=True)

    # Then only the second refused, and it ended with the hint
    assert str(raised.value).endswith(HINT)
