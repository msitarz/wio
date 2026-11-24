# SPDX-License-Identifier: Apache-2.0
"""Planning a new rule: its code, its place and its file, before anything is written."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import PurePosixPath

    from wio.models.rule import Rule
    from wio.rules.discovery import Discovery


@dataclass(frozen=True)
class NewRule:
    """What `wio rules new` is going to write.

    It is immutable and hashable.

    Attributes:
        path: Where the file goes, relative to the repository root and written
            with `/`.
        text: The whole file: a `<!-- wio -->` block with the code, the name and
            the description when there is one, and an empty body.
        rule: The rule that reading `text` at `path` gives.
    """

    path: PurePosixPath
    text: str
    rule: Rule


def plan_rule(
    ruleset: str,
    family: str,
    name: str,
    description: str | None,
    discovery: Discovery,
) -> NewRule:
    """Plan the next rule of a family in a ruleset.

    The code is the family's letters and the number after the highest number of
    the family, so a free number below it is not reused. The number has at least
    three digits and at least as many as the highest code of the family. The file
    is `<code>-<name>.md` in the directory of the rule with the highest code of
    the family, or in the ruleset's directory when the family has none, and its
    block is written in the comment form, whatever form the other rules have,
    with a quote, a backslash and `-->` of the description escaped. The text is
    read back with `read_rule`, so the plan is a valid rule. It does no input or
    output.

    Args:
        ruleset: The canonical name of a ruleset of the discovery.
        family: The upper-case letters of a family that the ruleset's manifest
            declares.
        name: The rule's name, in the form of a rule name.
        description: The one-line description, or `None` for none.
        discovery: What the walk of the rules found; its rulesets are those that
            were read whole.

    Returns:
        The path, the text and the rule.

    Raises:
        WioError: The ruleset is not one that was read, the family is not
            declared by its manifest, the name or the description is not of the
            right form, or the ruleset already has a rule with the name. It
            names the cause, and lists the rulesets, the families or the form
            that would do.
    """
    del ruleset, family, name, description, discovery
    raise NotImplementedError
