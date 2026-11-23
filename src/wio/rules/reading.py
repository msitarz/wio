# SPDX-License-Identifier: Apache-2.0
"""The reader of a rule file, which turns the text of one file into a `Rule`.

It does no input or output and reads only the text it is given, so the walking
of a directory and the judging of a rule against its ruleset are for the caller.
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import PurePosixPath

    from wio.models.diagnostics import Diagnostic
    from wio.models.rule import Rule

RULE_NAME_FORM = "lower-case words of letters and digits joined by single hyphens"
"""The form of a rule's name in words, as a message states it."""

RULE_NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
"""The form of a rule's name: words of letters and digits, hyphens between."""


@dataclass(frozen=True)
class RuleReading:
    """What reading one rule file gave.

    Attributes:
        rule: The rule, or `None` when the file is not a rule or has an error.
        diagnostics: Every error and warning of the file, each with its place,
            in the order a check of files prints them; empty for a file that is
            not marked.
    """

    rule: Rule | None
    diagnostics: tuple[Diagnostic, ...]


def read_rule(ruleset: str, path: PurePosixPath, text: str) -> RuleReading:
    """Read the text of a rule file into a rule.

    Reuses the code form `CODE` of `wio.formats.grammar`, the block reader
    `read_metadata_block` and `closest_key` of `wio.formats`.

    Args:
        ruleset: The name of the ruleset whose directory holds the file.
        path: The path of the file relative to the repository root, which is the
            place of every diagnostic, followed by `:<line>` when a fault has a
            line.
        text: The text of the file, decoded as UTF-8.

    Returns:
        The rule and no error for a marked file whose `code` and `name` have
        their forms, in either block form, with a warning for each key that the
        block does not know and the known key it is close to. Every fault of the
        file is reported together as an error and leaves the rule out. A text
        with no metadata block on its first line, or with `+++` front matter
        that has no `wio` key, is not a rule and gives no diagnostic.
    """
    del ruleset, path, text
    msg = "read_rule is declared by the architecture stage"
    raise NotImplementedError(msg)
