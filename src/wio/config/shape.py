# SPDX-License-Identifier: Apache-2.0
"""The shape of the config file: its keys, types and values, read from the schema."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic

type Source = Literal["file", "default"]


@dataclass(frozen=True)
class Shape:
    """What the walk of a decoded file built.

    Attributes:
        config: The best-effort `Config`: an invalid value has its default, an
            unknown key and an entry of the wrong type are dropped, and a root
            or an action that lacks a required key keeps it empty.
        diagnostics: One error for each problem of the shape, in no order.
        sources: The source of each leaf key path that has a value.
    """

    config: Config
    diagnostics: tuple[Diagnostic, ...]
    sources: frozendict[str, Source]


def read_shape(data: dict[str, object]) -> Shape:
    """Walk the dataclasses of `Config` over a decoded config file.

    One walk builds the value, the diagnostics of its shape and the source of
    each key path from the same schema, so none can drift from the fields.

    Args:
        data: The decoded file, as `decode_toml` returns it.

    Returns:
        The best-effort `Config`, every problem of the shape and the sources.
    """
    raise NotImplementedError
