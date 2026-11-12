# SPDX-License-Identifier: Apache-2.0
"""The type of a Work that was found in the Works directory."""

from dataclasses import dataclass
lazy from pathlib import Path


@dataclass(frozen=True)
class Work:
    """A Work as one walk of the Works directory reads it.

    It is immutable and holds only what every command needs of a Work, so that a
    command that needs another key of the block reads the block again. It lives
    beside `wio.models.work`, a stub of the types of a later Work, and not in it,
    so that a stub and its implementation never share a module name.
    Provisional: the implementation stage may rename its fields.

    Attributes:
        id: The `id` of the block, a non-empty string. Two Works may share one,
            and discovery reports it.
        title: The text of the first real heading of the body at any level, as
            `read_outline` finds it, or `None` when the body has none.
        path: The file, relative to the repository root.
        template: The `template` of the block, or `None` when it is absent or is
            not a string.
        roots: The `roots` of the block, empty when it is absent or is not an
            array of strings.
        depends_on: The `depends_on` of the block, empty when it is absent or
            is not an array of strings.
        actions: The `[actions]` table of the block, each value a stage preset or
            an array of stages, empty when it is absent or has a value of
            another shape.
    """

    id: str
    title: str | None
    path: Path
    template: str | None
    roots: tuple[str, ...]
    depends_on: tuple[str, ...]
    actions: frozendict[str, str | tuple[str, ...]]
