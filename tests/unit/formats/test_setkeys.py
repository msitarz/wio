# SPDX-License-Identifier: Apache-2.0
"""Tests of rewriting metadata blocks while retaining their values and body."""

import pytest

from wio.formats import read_metadata_block, set_block_keys
from wio.formats.errors import MetadataBlockError


@pytest.mark.parametrize("front", [False, True])
def test_rewrites_metadata_and_preserves_body(*, front: bool) -> None:
    """The identifier comes first and only metadata formatting is discarded."""
    # Given a block with comments and mixed endings and a body with a comment
    opening = "+++" if front else "<!-- wio"
    marker = "wio = 1\n" if front else ""
    close = "+++" if front else "-->"
    body = "\n\n<!-- body -->\r\n# Title\n"
    text = (
        f'{opening}\r\n{marker}template = "t" # metadata\n[x]\r\na = 1\n{close}{body}'
    )

    # When the id and a table are set
    result = set_block_keys(text, {"id": "k3m9xq"}, {"actions": {"run": ["x"]}})

    # Then the rewritten block has ordered values and the body is unchanged
    block = read_metadata_block(result)
    assert block is not None
    prefix = f"{opening}\r\n" + ("wio = 1\r\n" if front else "")
    assert result.startswith(prefix + 'id = "k3m9xq"\r\n')
    assert "# metadata" not in result
    assert "\n" not in result[: result.index(close)].replace("\r\n", "")
    assert result.endswith(body)
    assert block.data == {
        "id": "k3m9xq",
        "template": "t",
        "x": {"a": 1},
        "actions": {"run": ["x"]},
    }


def test_replaces_values_and_round_trips_toml_types() -> None:
    """Inline tables, nested tables, dates and strings retain their values."""
    # Given metadata with varied TOML values, including comments inside arrays
    text = (
        "<!-- wio\ninline = { a = 1 }\ndate = 2024-01-01\n"
        'array = ["# value", # comment\n "old"]\n[x]\nnote = "a\\nb"\n-->\n# T\n'
    )
    before = read_metadata_block(text)
    assert before is not None

    # When an array and table are replaced and a key is added
    result = set_block_keys(text, {"id": "new", "array": ["new"]}, {"x": {"b": 2}})

    # Then untouched values survive and metadata comments are discarded
    after = read_metadata_block(result)
    assert after is not None
    assert after.data == {**before.data, "id": "new", "array": ["new"], "x": {"b": 2}}
    assert "# comment" not in result
    assert after.body == before.body


def test_missing_block_is_refused() -> None:
    """A file without metadata cannot be edited."""
    # Given a body without a metadata block
    text = "# T\n"

    # When a key is set
    # Then the block reader's error is raised
    with pytest.raises(MetadataBlockError):
        set_block_keys(text, {"id": "k3m9xq"})


def test_byte_order_mark_and_crlf() -> None:
    """A byte-order mark and the body survive rewriting with CRLF."""
    # Given a CRLF block with a multiline value
    text = '\ufeff<!-- wio\r\nnote = """one\r\ntwo"""\r\n-->\r\n\r\n# T\r\n'
    before = read_metadata_block(text)
    assert before is not None

    # When a key and table are set
    result = set_block_keys(text, {"id": "k3m9xq"}, {"actions": {"deliver": ["x"]}})

    # Then CRLF, the original value, the mark and the body are retained
    after = read_metadata_block(result)
    assert after is not None
    assert result.startswith("\ufeff")
    assert "\n" not in result.replace("\r\n", "")
    assert after.data["note"] == before.data["note"]
    assert after.body == before.body
