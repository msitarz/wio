# SPDX-License-Identifier: Apache-2.0
"""The settings of a `Config` as a flat, sorted list, and the lines that show them."""

import dataclasses
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, cast

from wio.config.messages import join_path

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from wio.config.shape import Source
    from wio.models.config import Config

type Value = str | bool | int | tuple[str, ...]
"""What a setting holds: a string, a boolean, an integer or a list of strings."""

WIDTH: Final = 80
"""The columns a line of `list` fits in, unless its key path and label do not."""

_ELLIPSIS = "…"
_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
_SPECIAL = re.compile(r'[\\"\x00-\x1f\x7f]')


@dataclass(frozen=True)
class Setting:
    """One setting that has a value.

    Attributes:
        path: Its key path.
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
        The leaf settings; a table has none of its own and an optional setting
        that is not set is left out.
    """
    found = _walk(config, "", "", sources)
    return tuple(sorted(found, key=lambda setting: setting.path))


def _walk(
    node: object, path: str, description: str, sources: Mapping[str, Source]
) -> Iterator[Setting]:
    """Walk a node of the config and yield the settings below it.

    Args:
        node: A table, a table of named entries or a value.
        path: Its key path.
        description: The description of the setting that holds it.
        sources: The source of each key path.

    Yields:
        Each leaf setting that has a value.
    """
    match node:
        case None:
            return
        case frozendict():
            for name, entry in node.items():
                yield from _walk(entry, join_path(path, name), description, sources)
        case _ if dataclasses.is_dataclass(node):
            for item in dataclasses.fields(node):
                yield from _walk(
                    getattr(node, item.name),
                    join_path(path, item.name),
                    str(item.metadata["description"]),
                    sources,
                )
        case _:
            yield Setting(path, cast("Value", node), sources[path], description)


def quote(text: str) -> str:
    """Write a string as a TOML basic string on one line.

    Args:
        text: The string.

    Returns:
        The string in double quotes, its newlines, quotes, backslashes and
        control characters escaped.
    """
    return f'"{_escape(text)}"'


def _escape(text: str) -> str:
    """Escape what a TOML basic string cannot hold as it is.

    Args:
        text: The string.

    Returns:
        The string without its quotes.
    """
    return _SPECIAL.sub(
        lambda found: _ESCAPES.get(found.group(), f"\\u{ord(found.group()):04x}"),
        text,
    )


def toml_value(value: Value) -> str:
    """Write a value the way TOML does.

    Args:
        value: What a setting holds.

    Returns:
        The value in full: strings quoted, booleans as `true` and `false`, and a
        tuple as an array.
    """
    match value:
        case bool():
            return "true" if value else "false"
        case str():
            return quote(value)
        case tuple():
            return "[" + ", ".join(toml_value(item) for item in value) + "]"
        case _:
            return str(value)


def label(setting: Setting) -> str:
    """Write the source of a setting as the comment that ends its line.

    Args:
        setting: The setting.

    Returns:
        `  # file` or `  # default`.
    """
    return f"  # {setting.source}"


def full_line(setting: Setting) -> str:
    """Write a setting in full on one line.

    Args:
        setting: The setting.

    Returns:
        `key.path = value  # file`, with the value as TOML writes it.
    """
    return f"{setting.path} = {toml_value(setting.value)}{label(setting)}"


def short_line(setting: Setting) -> str:
    """Write a setting on one line of at most 80 columns where it can.

    Args:
        setting: The setting.

    Returns:
        `key.path = value  # file` with the value shortened to fit. A string
        of several lines shows its first line, then `…` before the closing
        quote. The key path and the label are always whole, so when they leave
        no room the value is `…` and the line is longer.
    """
    head = f"{setting.path} = "
    room = WIDTH - len(head) - len(label(setting))
    return f"{head}{_short(setting.value, room)}{label(setting)}"


def _short(value: Value, room: int) -> str:
    """Shorten a value to a number of columns.

    Args:
        value: The value.
        room: The columns it may take.

    Returns:
        The value, shortened as needed, or `…` when nothing else fits.
    """
    match value:
        case str():
            text = _short_string(value, room)
        case tuple():
            text = _short_array(value, room)
        case _:
            text = toml_value(value)
    return text if len(text) <= room else _ELLIPSIS


def _short_string(value: str, room: int) -> str:
    """Shorten a string to its first line, and to a number of columns.

    Args:
        value: The string.
        room: The columns it may take, quotes included.

    Returns:
        The string in quotes, with `…` before the closing quote when it was
        cut.
    """
    first, cut, _ = value.partition("\n")
    escaped = _escape(first)
    if cut:
        escaped += _ELLIPSIS
    elif len(escaped) + 2 > room:
        escaped = escaped[: max(room - 3, 0)] + _ELLIPSIS
    return f'"{escaped}"'


def _short_array(value: tuple[str, ...], room: int) -> str:
    """Shorten an array by dropping the items from its end.

    Args:
        value: The items.
        room: The columns it may take, brackets included.

    Returns:
        The array in full when it fits, otherwise as many leading items as fit
        followed by `…`.
    """
    items = [toml_value(item) for item in value]
    for count in range(len(items), -1, -1):
        text = _array(items, count)
        if len(text) <= room:
            return text
    return _ELLIPSIS


def _array(items: list[str], count: int) -> str:
    """Write the first items of an array, and `…` when others are left out.

    Args:
        items: The items, already in TOML syntax.
        count: How many of them to keep.

    Returns:
        The array in brackets.
    """
    kept = items[:count]
    if count < len(items):
        kept.append(_ELLIPSIS)
    return "[" + ", ".join(kept) + "]"


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
    return {
        item.path: {"value": item.value, "source": item.source}
        for item in sorted(settings, key=lambda setting: setting.path)
    }
