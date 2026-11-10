# SPDX-License-Identifier: Apache-2.0
"""The type of a template that was found in the templates directory."""

from dataclasses import dataclass
lazy from pathlib import Path


@dataclass(frozen=True)
class Template:
    """A template, as `wio.templates` finds it.

    It is immutable and holds what the metadata block says, judged only as far
    as building it needs: whether a key is the right type, not what it means.

    Attributes:
        name: The file's name without `.md`, which is how a config, a contract
            and a command refer to the template.
        kind: The kind the template belongs to, which the config may or may not
            declare.
        shape: The `shape` key, such as `leaf`, or `None` when the template has
            none.
        description: The `description` key as written, or `None` when the
            template has none.
        path: The file's path relative to the repository root.
        entry: Whether `[templates.kinds]` names this template as the entry
            template of its own kind.
    """

    name: str
    kind: str
    shape: str | None
    description: str | None
    path: Path
    entry: bool
