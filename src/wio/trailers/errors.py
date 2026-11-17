# SPDX-License-Identifier: Apache-2.0
"""The errors of `wio.trailers`."""

from wio.errors import WioError


class TrailersError(WioError):
    """A mistake in a `wio trailers` command that the user must fix.

    It carries the message that the command line prints after `error: `, and it
    exits 2, as every `WioError` does. It is for a call that no form of the
    command accepts, such as a Work that is a list, and never for a record whose
    fields do not hold, which a command reports itself and exits 1 for.
    """
