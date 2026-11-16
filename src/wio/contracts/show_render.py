# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts show` writes, as text or as JSON."""

from typing import TYPE_CHECKING

lazy from wio.formats import encode_json

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.contracts.showing import ShownAction, ShownWork


def render_show(shown: ShownWork, *, as_json: bool) -> str:
    """Render a Work for a person or for a program.

    It reads nothing and writes nothing, and imports `json` only for the JSON
    form.

    The text is the first line `Work <id>  <title>`, the facts, a blank line,
    `Actions` and the actions, a blank line, a line of `----`, a blank line and
    the view. The facts are `Path`, `Template`, `Parent`, `Roots`, `After` and
    `Needed by`, each written only when it has something to say, with its label
    padded so that every value starts at column 15 and a second value on the next
    line in that column. `Roots` shows a Work's own roots as written, and when it
    lists `@descendants` an arrow and the resolved roots, or `none`. A related
    Work is `<id>  <title>`, with `(not found)` and `(no title)` where they
    apply. An action is its name, its preset, where it comes from and `on demand`
    when the config marks it, with its stages on the next line, or `removed (by
    the contract)` with no mark, although the JSON keeps the config's flag. With
    no action line to print, `Actions` is followed by the line `none`, and the
    JSON `actions` is an empty array.

    The JSON is one object on one line, written by `json.dumps` with its default
    separators, with `id`, `title`, `path`, `template`, `parent`, `roots`,
    `resolved_roots`, `depends_on`, `dependents`, `actions` and `view` in that
    order. The text and the JSON say the same facts.

    Args:
        shown: The Work with what `gather_work` found.
        as_json: Whether to render the object instead of the text.

    Returns:
        The text for standard output, ending in one line ending.
    """
    if as_json:
        return f"{encode_json(_as_object(shown))}\n"
    head = [
        _first_line(shown),
        *_fact_lines(shown),
        "",
        "Actions",
        *_action_lines(shown.actions),
        "",
        "----",
        "",
    ]
    return "\n".join(head) + "\n" + shown.view


def _first_line(shown: ShownWork) -> str:
    """Write the first line of the text.

    Args:
        shown: The Work.

    Returns:
        `Work <id>  <title>`, with `(no title)` for a Work with none.
    """
    raise NotImplementedError


def _fact_lines(shown: ShownWork) -> list[str]:
    """Write the fact lines of the text.

    Args:
        shown: The Work.

    Returns:
        The lines of `Path`, `Template`, `Parent`, `Roots`, `After` and
        `Needed by` that have something to say, with the labels padded and a
        second value on a line of its own in the column of the first.
    """
    raise NotImplementedError


def _action_lines(actions: Sequence[ShownAction]) -> list[str]:
    """Write the lines of the actions block.

    Args:
        actions: The Work's actions in order.

    Returns:
        The lines of each action with its stages, or the one line `  none` when
        there is no action.
    """
    raise NotImplementedError


def _as_object(shown: ShownWork) -> dict[str, object]:
    """Describe a Work as plain data for JSON.

    Args:
        shown: The Work.

    Returns:
        The fields in the order of the contract, with `path` written with `/`.
    """
    raise NotImplementedError
