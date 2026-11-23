# SPDX-License-Identifier: Apache-2.0
"""The type of a rule that was read from a rule file."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import PurePosixPath

_FAMILY_AND_NUMBER = re.compile(r"([A-Z]+)([0-9]+)")


@dataclass(frozen=True)
class Rule:
    """One atomic do-or-don't instruction, read from a rule file.

    A rule is immutable and hashable, so it can be a key of a mapping. Two rules
    are equal when every field is.

    Attributes:
        ruleset: The name of the ruleset whose directory holds the file.
        code: The rule's code, a family of upper-case letters and digits, such
            as `ARC001`.
        name: The rule's name, lower-case words joined by single hyphens.
        description: The one-line description in the metadata block, if any.
        summary: The lines of the body's first paragraph, each stripped and
            joined with single spaces; empty when there is no body.
        body: The text after the metadata block without its leading and
            trailing blank lines and without a final line ending, with the line
            endings the file has.
        body_line: The line of the file, counted from 1, on which the body
            starts, or the line after the block when the body is empty.
        path: The path of the file as the reader was given it.
    """

    ruleset: str
    code: str
    name: str
    description: str | None
    summary: str
    body: str
    body_line: int
    path: PurePosixPath

    @property
    def family(self) -> str:
        """The upper-case letters of the code, such as `ARC`."""
        return self._parts()[0]

    @property
    def number(self) -> int:
        """The digits of the code as a number, such as 1 for `ARC001`."""
        return int(self._parts()[1])

    @property
    def qualified(self) -> str:
        """The code with its ruleset, such as `demo.ARC001`."""
        return f"{self.ruleset}.{self.code}"

    def _parts(self) -> tuple[str, str]:
        """Split the code into its family and its digits.

        Returns:
            The family and the digits; a rule read from a file always has a code
            of that form.
        """
        found = _FAMILY_AND_NUMBER.fullmatch(self.code)
        if found is None:
            message = f"`{self.code}` is not a family and digits"
            raise ValueError(message)
        return found[1], found[2]
