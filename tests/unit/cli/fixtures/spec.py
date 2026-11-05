# SPDX-License-Identifier: Apache-2.0
"""The command spec that both fixture command packages describe."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import ArgumentParser


class Spec:
    """A command spec with nothing to configure."""

    name = "fixture"
    help = "A fixture command."

    def configure(self, parser: ArgumentParser) -> None:
        """Add nothing to the subparser.

        Args:
            parser: The subparser, left as it is.
        """


def describe() -> Spec:
    """Describe the fixture command.

    Returns:
        Its spec.
    """
    return Spec()
