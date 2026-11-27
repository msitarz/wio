# SPDX-License-Identifier: Apache-2.0
"""Next step advisor (`wio next`) component.

Reads effective `Wio-*` records from git history, evaluates Work state and
staleness, and advises the next action and stage for each Work.
"""

from wio.next.history import EffectiveRecord, read_effective_records

__all__ = [
    "EffectiveRecord",
    "read_effective_records",
]
