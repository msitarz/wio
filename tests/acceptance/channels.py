# SPDX-License-Identifier: Apache-2.0
"""The channels a scenario can reach `wio` through."""

from enum import Enum


class Channel(Enum):
    """A way a scenario reaches `wio`.

    The value is the id of the pytest case that runs on the channel.
    """

    IN_PROCESS = "in_process"
    CLI = "cli"
