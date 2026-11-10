# SPDX-License-Identifier: Apache-2.0
"""The grammar of the directives on a heading, and the table that documents it."""

from wio.models.directives import DirectiveHeading, DirectiveSpec

DIRECTIVES: tuple[DirectiveSpec, ...] = (
    DirectiveSpec(
        name="required",
        syntax="required",
        meaning="The heading is present in the contract.",
        examples=("## Purpose <!-- wio: required -->",),
    ),
    DirectiveSpec(
        name="items",
        syntax="items>=N",
        meaning="The section holds at least N items, N being 1 or more.",
        examples=("## Goals <!-- wio: items>=1 -->",),
    ),
    DirectiveSpec(
        name="pattern",
        syntax='pattern=<regex> or pattern="<regex>"',
        meaning=(
            "The items of the section match the regular expression, and the "
            "matches are their item ids."
        ),
        examples=(
            "## Acceptance criteria <!-- wio: pattern=AC-\\d+ -->",
            '## Acceptance criteria <!-- wio: pattern="AC-\\d{1,3}" -->',
        ),
    ),
    DirectiveSpec(
        name="inherit",
        syntax="inherit",
        meaning="A descendant's resolved view includes the section.",
        examples=("## Glossary <!-- wio: inherit -->",),
    ),
)
"""Every directive in the order `required`, `items`, `pattern`, `inherit`."""


def read_directive_heading(line: str) -> DirectiveHeading | None:
    """Read one line as a heading with its directive list.

    A directive list opens with `<!--`, whitespace, the lowercase `wio:` and
    whitespace, ends at the first `-->`, and ends its heading. Any other comment
    is a note and stays in the text. The line is read alone: nothing is read
    from a file.

    Args:
        line: One line of Markdown, without its line ending.

    Returns:
        The heading's text, level and directives in the order written, with no
        directives for a heading without a list, or `None` for a line that is
        not an ATX heading.

    Raises:
        DirectiveSyntaxError: The list names an unknown directive or one in the
            wrong case or twice, is empty, does not close on the line, is
            followed by text or by a second list, or gives a directive a wrong
            value. It carries the column of the first problem.
    """
    raise NotImplementedError
