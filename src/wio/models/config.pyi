# SPDX-License-Identifier: Apache-2.0
"""The type for the project's settings.

The stub is the spec until the Work that implements `wio config` replaces it
with a `.py` of the same annotations. It declares no fields: the config schema
is that Work's to settle.
"""

class Config:
    """The effective settings read from `.agents/wio/config.toml`.

    It is immutable once loaded, so every component that holds it sees the same
    types, actions, roots, stages, presets, tags and results.
    """
