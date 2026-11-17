# SPDX-License-Identifier: Apache-2.0
"""The `wio trailers` command: writing and checking the records of commits."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.io.ports import FileSystem, History
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
        history: Gives the commits of a range with their messages.
        staged_contracts: Finds the Works in the index and then in `HEAD`, as the
            check of a commit message needs them, where `contracts` finds them in
            the working tree and then in `HEAD`.
        files: Reads the file that holds a message to check.
    """

    settings: Settings
    contracts: Contracts
    history: History
    staged_contracts: Contracts
    files: FileSystem
