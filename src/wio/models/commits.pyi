# SPDX-License-Identifier: Apache-2.0
"""The type for a commit as `wio.io.ports.Git` reports it.

The stub is the spec until the Work that first reads commits replaces it with a
`.py` of the same annotations. It declares no fields: the first Work that reads
a commit's id or message adds them.
"""

class Commit:
    """A commit's full id and its message.

    The id lets a reader name the exact commit that a gate reviewed or that a
    session started from, and the message carries the records.
    """
