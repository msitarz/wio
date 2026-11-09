# SPDX-License-Identifier: Apache-2.0
"""The channels a scenario can reach `wio` through."""

from enum import Enum

import pytest


class Channel(Enum):
    """A way a scenario reaches `wio`.

    The value is the id of the pytest case that runs on the channel.
    """

    IN_PROCESS = "in_process"
    CLI = "cli"


IN_BOTH = pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
"""A scenario that runs on both channels: the fast copy and the reference."""

CLI_ONLY = pytest.mark.channels(Channel.CLI)
"""A scenario that needs the command a user runs, such as an error scenario."""
