# SPDX-License-Identifier: Apache-2.0
"""Tests of editing metadata blocks without losing their contents."""

import pytest

from wio.formats import read_metadata_block, set_block_keys
from wio.formats.errors import MetadataBlockError


def test_sets_values_and_tables_without_losing_existing_data() -> None:
    """Both forms retain untouched values, comments, delimiters and body."""
    # Given comment and front matter blocks with a comment and a table
    texts = (
        '<!-- wio\ntemplate = "t"\nroots = []\n# keep\n[x]\na = 1\n-->\n\n# T\n',
        '+++\nwio = 1\ntemplate = "t"\nroots = []\n# keep\n[x]\na = 1\n+++\n\n# T\n',
    )

    # When keys and a table are set
    results = [
        set_block_keys(
            text,
            {"id": "k3m9xq", "roots": ["wio"]},
            {"actions": {"deliver": ["build"]}},
        )
        for text in texts
    ]

    # Then the values and unchanged contents remain readable in both forms
    for result in results:
        block = read_metadata_block(result)
        assert block is not None
        assert block.data == {
            "template": "t",
            "roots": ["wio"],
            "id": "k3m9xq",
            "x": {"a": 1},
            "actions": {"deliver": ["build"]},
        }
        assert "# keep" in result
        assert block.body == "\n# T\n"


def test_crlf_and_multiline_values_are_preserved() -> None:
    """Added lines use CRLF without changing a multiline TOML value."""
    # Given a CRLF block with a multiline value
    text = '\ufeff<!-- wio\r\nnote = """one\r\ntwo"""\r\n-->\r\n\r\n# T\r\n'
    before = read_metadata_block(text)
    assert before is not None

    # When a key and table are set
    result = set_block_keys(text, {"id": "k3m9xq"}, {"actions": {"deliver": ["x"]}})

    # Then all endings remain CRLF and the original value and body are retained
    after = read_metadata_block(result)
    assert after is not None
    assert result.startswith("\ufeff")
    assert "\n" not in result.replace("\r\n", "")
    assert after.data["note"] == before.data["note"]
    assert after.body == before.body


def test_plain_keys_and_tables_do_not_replace_each_other() -> None:
    """Conflicting names are refused."""
    # Given an inline table and a standard table
    inline = "<!-- wio\nactions = { a = 1 }\n-->\n"
    table = "<!-- wio\n[x]\na = 1\n-->\n"

    # When the other form is set under the same name
    # Then both calls are refused
    with pytest.raises(ValueError, match="plain key"):
        set_block_keys(inline, {}, {"actions": {"a": 2}})
    with pytest.raises(ValueError, match="is a table"):
        set_block_keys(table, {"x": "value"})


def test_missing_block_is_refused() -> None:
    """A file without metadata cannot be edited."""
    # Given a body without a metadata block
    text = "# T\n"

    # When a key is set
    # Then the block reader's error is raised
    with pytest.raises(MetadataBlockError):
        set_block_keys(text, {"id": "k3m9xq"})


def test_mixed_endings_and_arrays_of_mappings() -> None:
    """Existing endings survive replacements, and mappings in arrays stay inline."""
    # Given a block with mixed endings and a value to replace
    text = '<!-- wio\r\nid = "old"\nother = 1\r\n-->\n'

    # When the id is replaced and an array of mappings is added
    result = set_block_keys(text, {"id": "new", "items": [{"value": 2}]})

    # Then existing endings and the array's plain-key form are retained
    assert 'id = "new"\n' in result
    assert "other = 1\r\n" in result
    assert "items = [{value = 2}]\r\n" in result
    assert "[[items]]" not in result


def test_replacing_a_table_preserves_comments_and_other_tables() -> None:
    """Replacing a table keeps its comments and the following table."""
    # Given a table with header, entry and trailing comments before another table
    text = "<!-- wio\n[x] # header\na = 1 # entry\n# about y\n[y]\nb = 2\n-->\n\n# T\n"

    # When the first table is replaced
    result = set_block_keys(text, {}, {"x": {"new": 3}})

    # Then all comments remain and the values reflect the replacement
    block = read_metadata_block(result)
    assert block is not None
    assert block.data == {"x": {"new": 3}, "y": {"b": 2}}
    assert all(comment in result for comment in ("# header", "# entry", "# about y"))
    assert block.body == "\n# T\n"


def test_inline_mappings_and_empty_blocks() -> None:
    """An empty block accepts an id and a mapping as an inline value."""
    # Given an empty metadata block
    text = "<!-- wio\n-->\n\n# T\n"

    # When a plain key with a mapping and an id are set
    result = set_block_keys(text, {"id": "k3m9xq", "details": {"a": 1}})

    # Then the id and inline table are readable as plain keys
    block = read_metadata_block(result)
    assert block is not None
    assert block.data == {"id": "k3m9xq", "details": {"a": 1}}
    assert "details = {" in result
    assert "[details]" not in result


def test_multiline_and_dotted_values_survive_adding_a_key() -> None:
    """A dotted key and a multiline string are retained when a key is added."""
    # Given a block with a dotted key and a multiline string containing comments
    text = '<!-- wio\na.b = 1\n[x]\nnote = """one\n\n# not a comment\nend"""\n-->\n'
    before = read_metadata_block(text)
    assert before is not None

    # When a key is added
    result = set_block_keys(text, {"id": "k3m9xq"})

    # Then the old values and the new id are present
    after = read_metadata_block(result)
    assert after is not None
    assert after.data == {**before.data, "id": "k3m9xq"}
