# SPDX-License-Identifier: Apache-2.0
"""The types of a heading's directives and of the table that documents them."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Required:
    """`required`: the heading is present in the contract."""


@dataclass(frozen=True)
class Items:
    """`items>=N`: the section holds at least `minimum` items.

    Attributes:
        minimum: The least number of items, 1 or more.
    """

    minimum: int


@dataclass(frozen=True)
class Pattern:
    """`pattern=<regex>`: the items of the section match the expression.

    Attributes:
        regex: The expression as written, which `re` compiles.
    """

    regex: str


@dataclass(frozen=True)
class Inherit:
    """`inherit`: a descendant's resolved view includes the section."""


type Directive = Required | Items | Pattern | Inherit


@dataclass(frozen=True)
class DirectiveHeading:
    """A heading line read with its directives.

    Attributes:
        text: The heading's text after the `#` characters and the space, with
            any directive list and the space before it taken out and any other
            comment kept.
        level: The number of `#` characters, 1 to 6.
        directives: The directives in the order written, empty for a heading
            without a directive list.
    """

    text: str
    level: int
    directives: tuple[Directive, ...]


@dataclass(frozen=True)
class DirectiveSpec:
    """One entry of the table of directives.

    Attributes:
        name: The directive's lowercase name.
        syntax: How the directive is written, such as `items>=N`.
        meaning: What the directive says about a section, in one sentence.
        examples: Whole heading lines, one for each form the directive can be
            written in, which the parser reads into this directive.
    """

    name: str
    syntax: str
    meaning: str
    examples: tuple[str, ...]
