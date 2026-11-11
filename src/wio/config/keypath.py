# SPDX-License-Identifier: Apache-2.0
"""Finding what a key path names in a `Config`, or saying why it names nothing."""

import dataclasses
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from wio.config.messages import and_list, join_path, quoted
from wio.errors import ConfigurationError
lazy from wio.formats import closest_key

if TYPE_CHECKING:
    from collections.abc import Sequence

    from _typeshed import DataclassInstance

    from wio.models.config import Config

_TOP = "the top level of the config"
_NAME = r'(?:[A-Za-z0-9_-]+|"(?:[^"\\]|\\.)*")'
_PATH = re.compile(rf"{_NAME}(?:\[\d+\])*(?:\.{_NAME}(?:\[\d+\])*)*")
_ITEM = re.compile(rf"({_NAME})((?:\[\d+\])*)")


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
            True when it is the target itself or inside the target's table.
        """
        if self.single:
            return path == self.path
        return not self.path or path.startswith(f"{self.path}.")


def resolve(config: Config, key: str) -> Target:
    """Find what a key path names in a config.

    Args:
        config: The effective settings.
        key: A key path such as `stages.define.goal`; empty for the whole
            config.

    Returns:
        The target: one setting, or a table, which may be empty.

    Raises:
        ConfigurationError: The key path is malformed, names nothing (the
            message names the closest match and the valid keys), names an
            optional setting that is not set, or reaches into a list.
    """
    node: object = config
    path = ""
    for name, indices in _parse(key):
        node = _child(node, path, name)
        path = join_path(path, name)
        _check_value(node, path, indices)
    return Target(path, single=not _is_table(node))


def _parse(key: str) -> list[tuple[str, tuple[int, ...]]]:
    """Split a key path into its keys and the list indices that follow them.

    Args:
        key: The key path, with TOML's quoting of a key that needs it.

    Returns:
        Each key and its indices, none for an empty key path.

    Raises:
        ConfigurationError: The key path is not made of keys joined by dots.
    """
    if key and not _PATH.fullmatch(key):
        raise _malformed(key)
    parts = []
    for found in _ITEM.finditer(key):
        name = found.group(1)
        if name.startswith('"'):
            name = re.sub(r"\\(.)", r"\1", name[1:-1])
        parts.append((name, tuple(int(n) for n in re.findall(r"\d+", found.group(2)))))
    return parts


def _malformed(key: str) -> ConfigurationError:
    """Build the error of a key path that cannot be read.

    Args:
        key: The key path.

    Returns:
        An error that shows how to write one.
    """
    return ConfigurationError(
        f"`{key}` is not a key path. Write keys joined by dots, such as "
        "`stages.define.goal`, and quote a key that holds anything but letters, "
        'digits, `_` and `-`, as in `stages."a.b"`.'
    )


def _is_table(node: object) -> bool:
    """Tell whether a node is a table or a table of named entries.

    Args:
        node: A node of the config.

    Returns:
        True for a table and a table of named entries.
    """
    return isinstance(node, frozendict) or (
        dataclasses.is_dataclass(node) and not isinstance(node, type)
    )


def _entries(node: object) -> dict[str, object] | None:
    """List the keys of a table and their values.

    Args:
        node: A node of the config.

    Returns:
        The keys of a table or of a table of named entries, and `None` for a
        value, which has no keys.
    """
    match node:
        case frozendict():
            return {str(name): entry for name, entry in node.items()}
        case _ if _is_table(node):
            return {
                item.name: getattr(node, item.name)
                for item in dataclasses.fields(cast("DataclassInstance", node))
            }
        case _:
            return None


def _child(node: object, path: str, name: str) -> object:
    """Step from a table to one of its keys.

    Args:
        node: The node to step from.
        path: Its key path.
        name: The key to step to.

    Returns:
        The value of the key.

    Raises:
        ConfigurationError: The node has no such key, or is no table.
    """
    entries = _entries(node)
    if entries is None:
        message = f"`{path}` is a setting, so it has no key `{name}`."
        raise _refusal(message)
    if name not in entries:
        raise _unknown(path, name, list(entries))
    return entries[name]


def _refusal(message: str) -> ConfigurationError:
    """Build the error of a key path that cannot be shown.

    Args:
        message: What is wrong and what to do.

    Returns:
        The error, which the command line reports as the user's to fix.
    """
    return ConfigurationError(message)


def _unknown(path: str, name: str, names: Sequence[str]) -> ConfigurationError:
    """Build the error of a key a table does not have.

    Args:
        path: The key path of the table.
        name: The key asked for.
        names: The keys the table has.

    Returns:
        An error that names the closest match, if any, and the valid keys.
    """
    wanted = join_path(path, name)
    where = f"`{path}`" if path else _TOP
    message = f"no setting `{wanted}`."
    close = closest_key(name, names)
    if close:
        message += f" Did you mean `{join_path(path, close)}`?"
    if len(names) == 1:
        message += f" The only key of {where} is {quoted(names)}."
    elif names:
        message += f" The keys of {where} are {and_list([quoted([n]) for n in names])}."
    else:
        message += f" {where.capitalize()} has no entries."
    return ConfigurationError(message)


def _check_value(node: object, path: str, indices: tuple[int, ...]) -> None:
    """Refuse an optional setting that is not set, and an index into a list.

    Args:
        node: The value at the key path.
        path: The key path.
        indices: The list indices that followed the last key.

    Raises:
        ConfigurationError: The setting is not set, or an index follows a key
            that holds a list or no list.
    """
    if node is None:
        message = (
            f"`{path}` is an optional setting and it is not set, so there is "
            "nothing to show."
        )
        raise _refusal(message)
    if not indices:
        return
    if isinstance(node, tuple):
        message = f"a list is shown whole, so ask for `{path}`, not an item of it."
        raise _refusal(message)
    message = f"`{path}` is not a list, so it has no items."
    raise _refusal(message)
