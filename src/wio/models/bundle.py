# SPDX-License-Identifier: Apache-2.0
"""The compiled context bundle, which the composition hands to the command.

It is not `wio.models.config.Bundle`, which holds the settings of how a bundle
is joined.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class CompiledBundle:
    """A finished bundle with what its delivery and its record need.

    Attributes:
        text: The whole bundle, as it is delivered.
        id: The bundle id that the text states.
        size: The size of the bundle's body in UTF-8 bytes.
        rules: The `rule_hash` of the file of each rule the bundle prints, by
            qualified code, in the order printed.
    """

    text: str
    id: str
    size: int
    rules: Mapping[str, str]
