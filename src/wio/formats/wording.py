# SPDX-License-Identifier: Apache-2.0
"""The key path of a fault and the words of a list of names in a message.

`wio.config` and `wio.rules` write a place and a list with these functions, so
both read the same.
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

_BARE = re.compile(r"[A-Za-z0-9_-]+")


def join_path(parent: str, key: str) -> str:
    """Add a key to a key path, quoting it as TOML does when it needs it.

    Args:
        parent: The key path so far; empty at the top level.
        key: The key to add.

    Returns:
        The longer key path.
    """
    name = key if _BARE.fullmatch(key) else quote_string(key)
    return f"{parent}.{name}" if parent else name


def quote_string(text: str) -> str:
    """Quote text as a TOML basic string.

    Args:
        text: The key or the value.

    Returns:
        The text in double quotes, with backslashes and quotes escaped.
    """
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def item_path(parent: str, index: int) -> str:
    """Add a list index to a key path.

    Args:
        parent: The key path of the list.
        index: The position of the item.

    Returns:
        The key path of the item, such as `rules_include[0]`.
    """
    return f"{parent}[{index}]"


def quoted(names: Sequence[str]) -> str:
    """Join names in code quotes for a sentence.

    Args:
        names: The names.

    Returns:
        Each name in backticks, joined by commas.
    """
    return ", ".join(f"`{name}`" for name in names)


def declared(label: str, none: str, names: Sequence[str]) -> str:
    """List what is declared, or say that nothing is.

    Args:
        label: The words that start the list, such as `Declared stages`.
        none: The sentence for no name, such as `No stages are declared.`.
        names: The names, in the order to list them.

    Returns:
        "<label>: `a`, `b`." for some names, and `none` for none.
    """
    return f"{label}: {quoted(names)}." if names else none


def and_list(items: Sequence[str]) -> str:
    """Join items as English does.

    Args:
        items: The items, at least one.

    Returns:
        `a`, `a and b` or `a, b and c`.
    """
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"
