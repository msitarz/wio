# SPDX-License-Identifier: Apache-2.0
"""The `wio trailers` command: writing and checking the records of commits."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.ports import Settings
    from wio.trailers.ports import Contracts


@dataclass(frozen=True)
class Services:
    """What a form of `wio trailers` reads the project through.

    Provisional: a leaf that needs another port adds a field, and `wio.cli` builds
    the value from the adapters.

    Attributes:
        settings: Loads the config.
        contracts: Finds the items and the pipelines of the Works that a record
            names.
    """

    settings: Settings
    contracts: Contracts
