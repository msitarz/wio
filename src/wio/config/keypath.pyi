# SPDX-License-Identifier: Apache-2.0
"""Finding what a key path names in a `Config`, or saying why it names nothing.

The stub is the spec until the implementation stage replaces it with a `.py` of
the same annotations. Every refusal is a `ConfigurationError`, whose message
says what is wrong and what to ask for instead, so a person or an agent can
correct the key path in one turn.
"""

from dataclasses import dataclass

from wio.models.config import Config

@dataclass(frozen=True)
class Target:
    """What a key path names.

    Attributes:
        path: The key path in its canonical form, empty for the whole config.
        single: Whether it names one setting, rather than a table, which may
            hold no setting at all.
    """

    path: str
    single: bool

    def covers(self, path: str) -> bool:
        """Tell whether a setting is what the target names or is below it.

        Args:
            path: The key path of a setting.

        Returns:
            True when it is the target itself, or the target is a table that
            holds it. A key path that merely starts with the target's name, such
            as `stages.define2` for `stages.define`, is not covered.
        """
        ...

def resolve(config: Config, key: str) -> Target:
    """Find what a key path names in a config.

    Args:
        config: The effective settings.
        key: A key path such as `stages.define.goal`, with TOML's quoting for a
            key that needs it; empty for the whole config.

    Returns:
        The target: one setting, or a table, which may be empty. It judges the
        key path by the fields of the `Config` alone, so a table that holds no
        entry, such as `roots` of a config without roots, is a valid empty table
        and not an unknown key.

    Raises:
        ConfigurationError: The key path is malformed, and the message shows how
            to write one; or it names nothing, and the message gives the closest
            match and the valid keys of the table it stopped at; or it names an
            optional setting that is not set; or it asks for an item of a list,
            which is shown whole, and the message names the list's own key path;
            or it asks for an item of something that is no list, or for a key
            below a setting.
    """
    ...
