# SPDX-License-Identifier: Apache-2.0
"""Tests of the preparation of a skeleton in `wio.formats`."""

import pytest

from wio.errors import WioError
lazy from wio.formats import (
    DirectiveSyntaxError,
    MetadataBlockError,
    NotATemplateError,
    TemplateDirectiveError,
    prepare_skeleton,
)

COMMENT_TEMPLATE = """\
<!-- wio
# A comment of the author
kind = "feature"
shape = "leaf"
description = "A capability."

[actions]
deliver = "typed-boundary"

[contract]
roots = []
depends_on = []

[contract.x]
ticket = ""  # to fill in
-->

# <Work name>

## Goals <!-- wio: required, items>=1 -->
"""

FRONT_MATTER_TEMPLATE = """\
+++
wio = 1
kind = "feature"
shape = "leaf"
description = "A capability."

[actions]
deliver = "typed-boundary"

[contract]
roots = []
depends_on = []

[contract.x]
ticket = ""
+++

# <Work name>

## Goals <!-- wio: required, items>=1 -->
"""

CONTRACT_BODY = """\
# <Work name>

## Goals
"""


def test_a_comment_template_gives_a_comment_skeleton() -> None:
    """AC-1: the template's own keys, the directives and the comments are gone."""
    # Given the name `feature.leaf` and a comment template with its own keys,
    # `[contract]`, a sub-table, a comment and a directive list
    template = COMMENT_TEMPLATE

    # When the skeleton is prepared, and again
    first = prepare_skeleton("feature.leaf", template)
    second = prepare_skeleton("feature.leaf", template)

    # Then it is a comment block with `template` and the contract's keys, with no
    # own key, comment or marker, the heading has lost its list, and the two
    # results are equal
    assert first == (
        '<!-- wio\ntemplate = "feature.leaf"\nroots = []\ndepends_on = []\n\n'
        '[x]\nticket = ""\n-->\n\n' + CONTRACT_BODY
    )
    assert first == second


def test_a_front_matter_template_gives_a_front_matter_skeleton_with_the_marker() -> (
    None
):
    """AC-2: `+++` front matter whose first key is `wio = 1`."""
    # Given the same template written as `+++` front matter
    template = FRONT_MATTER_TEMPLATE

    # When the skeleton is prepared
    skeleton = prepare_skeleton("feature.leaf", template)

    # Then it is `+++` front matter with the marker first, then `template`, and
    # the same keys as the comment skeleton
    assert skeleton == (
        '+++\nwio = 1\ntemplate = "feature.leaf"\nroots = []\ndepends_on = []\n\n'
        '[x]\nticket = ""\n+++\n\n' + CONTRACT_BODY
    )


def test_the_metadata_is_template_and_the_contract_keys_and_no_id() -> None:
    """AC-3: `template` first, the keys in order, then the sub-tables."""
    # Given a template whose `[contract]` holds an `id`, a `template`, a key and
    # a sub-table, and which has its own keys
    template = (
        '<!-- wio\nkind = "k"\nshape = "leaf"\n[actions]\na = 1\n'
        '[contract]\nid = "zzzzzz"\ntemplate = "other"\nroots = ["wio"]\n'
        "[contract.y]\nn = 1\n-->\n"
    )

    # When the skeleton is prepared under the name `feature.leaf`
    skeleton = prepare_skeleton("feature.leaf", template)

    # Then the metadata is `template`, the key and the sub-table in that order,
    # with no `id` and none of the template's own keys
    assert skeleton == (
        '<!-- wio\ntemplate = "feature.leaf"\nroots = ["wio"]\n\n[y]\nn = 1\n-->\n'
    )


def test_a_template_without_a_contract_table_gives_only_template() -> None:
    """AC-3: no `[contract]` gives the `template` key alone."""
    # Given a template with its own keys and no `[contract]` table
    template = '<!-- wio\nkind = "k"\n[actions]\na = 1\n-->\n'

    # When the skeleton is prepared
    skeleton = prepare_skeleton("x", template)

    # Then the metadata is `template` alone
    assert skeleton == '<!-- wio\ntemplate = "x"\n-->\n'


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("## Purpose <!-- wio: required -->\n", "## Purpose\n"),
        (
            "<!--\nWrite it.\n## X <!-- wio: required -->\n-->\n",
            "<!--\nWrite it.\n## X <!-- wio: required -->\n-->\n",
        ),
        (
            "```\n## X <!-- wio: required -->\n```\n",
            "```\n## X <!-- wio: required -->\n```\n",
        ),
        ("## Note <!-- a note -->\n", "## Note <!-- a note -->\n"),
        (
            "## Both <!-- a note --> <!-- wio: required -->\n",
            "## Both <!-- a note -->\n",
        ),
        (
            "## A <!-- wio: required -->\r\ntext\r\n## B <!-- wio: inherit -->\r\n",
            "## A\r\ntext\r\n## B\r\n",
        ),
    ],
    ids=["list", "comment", "fence", "note", "note-then-list", "crlf"],
)
def test_the_body_keeps_everything_but_the_directive_lists(
    body: str, expected: str
) -> None:
    """AC-4: lists on real headings go, with the spaces before them."""
    # Given a template whose body is the case
    template = '<!-- wio\nkind = "k"\n-->\n' + body

    # When the skeleton is prepared
    skeleton = prepare_skeleton("x", template)

    # Then only the lists of real headings are gone
    assert skeleton == '<!-- wio\ntemplate = "x"\n-->\n' + expected


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        (
            '<!-- wio\r\nkind = "k"\r\n-->\r\n# T\r\n',
            '<!-- wio\r\ntemplate = "x"\r\n-->\r\n# T\r\n',
        ),
        ('<!-- wio\nkind = "k"\n-->', '<!-- wio\ntemplate = "x"\n-->\n'),
        ('<!-- wio\nkind = "k"\n-->\n# T\n', '<!-- wio\ntemplate = "x"\n-->\n# T\n'),
        (
            '﻿<!-- wio\nkind = "k"\n-->\n# T\n',
            '﻿<!-- wio\ntemplate = "x"\n-->\n# T\n',
        ),
    ],
    ids=["crlf", "empty-body", "lf", "byte-order-mark"],
)
def test_the_block_and_the_body_join_with_the_line_ending_of_the_template(
    template: str, expected: str
) -> None:
    """AC-4: the block uses the first line's ending, and an empty body is the block."""
    # Given a template that is the case
    # When the skeleton is prepared under the name `x`
    skeleton = prepare_skeleton("x", template)

    # Then the block and the body are joined as the case says
    assert skeleton == expected


def test_a_text_with_no_block_is_not_a_template() -> None:
    """AC-5: a text without a metadata block is refused as not a template."""
    # Given a text that has no metadata block, and front matter that is not wio's
    texts = ["# Title\n", '+++\nkind = "k"\n+++\n']

    # When the skeleton is prepared from each
    for text in texts:
        with pytest.raises(NotATemplateError) as caught:
            prepare_skeleton("x", text)

        # Then it raises an error that says it is not a template
        assert isinstance(caught.value, WioError)
        assert "not a template" in str(caught.value)


def test_a_block_that_does_not_close_raises_the_error_of_the_block_reader() -> None:
    """AC-5: the block reader's error is not changed, and names line 1."""
    # Given a comment block that does not close
    text = '<!-- wio\nkind = "k"\n'

    # When the skeleton is prepared
    with pytest.raises(MetadataBlockError) as caught:
        prepare_skeleton("x", text)

    # Then it raises the block reader's error naming line 1
    assert caught.value.line == 1


def test_a_wrong_directive_list_names_the_column_and_the_line_of_its_heading() -> None:
    """AC-5: the heading's line comes from the outline, so it is not line 1."""
    # Given a template whose heading on line 6 has the list `wio: mandatory`
    text = '<!-- wio\nkind = "k"\n-->\n\ntext\n## Bad <!-- wio: mandatory -->\n'

    # When the skeleton is prepared
    with pytest.raises(TemplateDirectiveError) as caught:
        prepare_skeleton("x", text)

    # Then it raises the directive parser's error with the column of the problem
    # and the line of the heading in the text
    error = caught.value
    assert isinstance(error, DirectiveSyntaxError)
    assert (error.line, error.column) == (6, 18)
    assert str(error).endswith("(line 6, column 18)")
