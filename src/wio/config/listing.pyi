# SPDX-License-Identifier: Apache-2.0
"""The settings of a `Config` as a flat, sorted list, and the lines that show them.

The stub is the spec until the implementation stage replaces it with a `.py` of
the same annotations. A line is written in TOML syntax, so a person or an agent
can read a value as the config file would hold it.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final

from wio.config.shape import Source
from wio.models.config import Config

type Value = str | bool | int | tuple[str, ...]
"""What a setting holds: a string, a boolean, an integer or a list of strings."""

WIDTH: Final = 80
"""The columns a line of `list` fits in, unless its key path and label do not."""

@dataclass(frozen=True)
class Setting:
    """One setting that has a value.

    Attributes:
        path: Its key path, with a key that needs it quoted as TOML quotes it.
        value: What it holds.
        source: Whether the `value` comes from the `file` or is the `default`.
        description: The one-sentence description of the setting.
    """

    path: str
    value: Value
    source: Source
    description: str

def settings_of(config: Config, sources: Mapping[str, Source]) -> tuple[Setting, ...]:
    """List every setting of a config that has a value, sorted by key path.

    Args:
        config: The effective settings.
        sources: The source of each key path, as `Loaded.sources` has it.

    Returns:
        The leaf settings, one for each key path in `sources`. A table has none
        of its own, a list is one setting, and an optional setting that is not
        set is left out.
    """
    ...

def quote(text: str) -> str:
    """Write a string as a TOML basic string on one line.

    Args:
        text: The string.

    Returns:
        The string in double quotes, its newlines, quotes, backslashes and
        control characters escaped, so the result has no line break.
    """
    ...

def toml_value(value: Value) -> str:
    """Write a value the way TOML does.

    Args:
        value: What a setting holds.

    Returns:
        The value in full: strings quoted, booleans as `true` and `false`, and a
        tuple as an array.
    """
    ...

def full_line(setting: Setting) -> str:
    """Write a setting in full on one line.

    Args:
        setting: The setting.

    Returns:
        `key.path = value  # file` or `# default`, with nothing shortened.
    """
    ...

def short_line(setting: Setting) -> str:
    """Write a setting on one line of at most `WIDTH` columns where it can.

    Args:
        setting: The setting.

    Returns:
        `key.path = value  # file` with the value shortened to fit. A string of
        several lines shows its first line then `…` before the closing quote,
        a single line that is too long is cut with `…` before the closing
        quote, and an array that does not fit keeps its leading items then `…`. The key
        path and the label are always whole, so when they leave no room the
        value is `…` and the line is longer than `WIDTH`.
    """
    ...

def as_object(settings: Iterable[Setting]) -> dict[str, dict[str, object]]:
    """Describe settings as the object that `--json` prints.

    Args:
        settings: The settings, in any order.

    Returns:
        A mapping from each key path, in key-path order, to `{"value": ...,
        "source": "file" | "default"}`. A value is never shortened, and a tuple
        stays a tuple, which `json.dumps` writes as a JSON array. It imports no
        module: the caller serializes it, so `json` is loaded only with
        `--json`.
    """
    ...
