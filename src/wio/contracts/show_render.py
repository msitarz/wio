# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts show` writes, as text or as JSON."""

from typing import TYPE_CHECKING, Final

lazy from wio.formats import encode_json

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.contracts.showing import Related, ShownAction, ShownSource, ShownWork

_LABEL_WIDTH: Final = 13
"""The width of a fact's label, so that every value starts at column 15."""
_NO_TITLE: Final = "(no title)"
_NOT_FOUND: Final = "(not found)"
_DESCENDANTS: Final = "@descendants"
_SOURCE_TEXT: Final[dict[ShownSource, str]] = {
    "template": "from the template",
    "contract": "from the contract",
    "defaults": "from the config defaults",
}
"""What an action's source is called in the text."""


def render_show(shown: ShownWork, *, as_json: bool) -> str:
    """Render a Work for a person or for a program.

    It reads nothing and writes nothing, and imports `json` only for the JSON
    form.

    The text is the first line `Work <id>  <title>`, the facts, a blank line,
    `Actions` and the actions, a blank line, a line of `----`, a blank line and
    the view, and ends at the line of `----` when the view is empty, so it
    always ends in one line ending. The facts are `Path`, `Template`, `Parent`,
    `Roots`, `After` and `Needed by`, each written only when it has something to
    say, with its label padded so that every value starts at column 15 and a
    second value on the next line in that column. `Roots` shows a Work's own
    roots as written, and when it lists `@descendants` an arrow and the resolved
    roots, or `none`. A related Work is `<id>  <title>`, with `(not found)` and
    `(no title)` where they apply. An action is its name, its preset, where it
    comes from and `on demand` when the config marks it, with its stages on the
    next line, or `removed (by the contract)` with no mark, although the JSON
    keeps the config's flag. With no action line to print, `Actions` is followed
    by the line `none`, and the JSON `actions` is an empty array.

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
    ]
    text = "\n".join(head) + "\n"
    return f"{text}\n{shown.view}" if shown.view else text


def _first_line(shown: ShownWork) -> str:
    """Write the first line of the text.

    Args:
        shown: The Work.

    Returns:
        `Work <id>  <title>`, with `(no title)` for a Work with none.
    """
    work = shown.work
    return f"Work {work.id}  {_NO_TITLE if work.title is None else work.title}"


def _fact_lines(shown: ShownWork) -> list[str]:
    """Write the fact lines of the text.

    Args:
        shown: The Work.

    Returns:
        The lines of `Path`, `Template`, `Parent`, `Roots`, `After` and
        `Needed by` that have something to say, with the labels padded and a
        second value on a line of its own in the column of the first. `Roots`
        is the Work's own `roots` as written, and `resolved_roots` only after the
        arrow of a Work that lists `@descendants`.
    """
    work = shown.work
    facts: list[tuple[str, list[str]]] = [
        ("Path", [work.path.as_posix()]),
        ("Template", [] if work.template is None else [work.template]),
        ("Parent", [] if shown.parent is None else [_related(shown.parent)]),
        ("Roots", _roots(shown)),
        ("After", [_related(related) for related in shown.depends_on]),
        ("Needed by", [_related(related) for related in shown.dependents]),
    ]
    return [line for label, values in facts for line in _rows(label, values)]


def _rows(label: str, values: Sequence[str]) -> list[str]:
    """Lay out the values of one fact under its label.

    Args:
        label: The fact's label.
        values: Its values, none for a fact with nothing to say.

    Returns:
        A line for each value, the label on the first and blanks of its width on
        the rest, so that every value starts at column 15.
    """
    return [
        f"  {label if index == 0 else '':<{_LABEL_WIDTH}}{value}"
        for index, value in enumerate(values)
    ]


def _related(related: Related) -> str:
    """Write a related Work as `<id>  <title>`.

    Args:
        related: The Work, or the id that no Work has.

    Returns:
        The id and the title, `(no title)` for a Work with none and
        `(not found)` for an id no Work has.
    """
    if not related.found:
        return f"{related.id}  {_NOT_FOUND}"
    return f"{related.id}  {_NO_TITLE if related.title is None else related.title}"


def _roots(shown: ShownWork) -> list[str]:
    """Write the roots of a Work.

    Args:
        shown: The Work.

    Returns:
        Nothing for a Work with no roots, otherwise one value: the roots as
        written, and for a Work that lists `@descendants` an arrow and what they
        resolve to, or `none`.
    """
    roots = shown.work.roots
    if not roots:
        return []
    text = ", ".join(roots)
    if _DESCENDANTS in roots:
        text += f" \u2192 {', '.join(shown.resolved_roots) or 'none'}"
    return [text]


def _action_lines(actions: Sequence[ShownAction]) -> list[str]:
    """Write the lines of the actions block.

    Args:
        actions: The Work's actions in order.

    Returns:
        The lines of each action with its stages, or the one line `  none` when
        there is no action.
    """
    if not actions:
        return ["  none"]
    width = max(len(action.name) for action in actions) + 2
    return [line for action in actions for line in _action(action, width)]


def _action(action: ShownAction, width: int) -> list[str]:
    """Write one action and its stages.

    Args:
        action: The action.
        width: The width of the name column.

    Returns:
        The line with the name, the preset and, in parentheses, where it comes
        from, or `removed (by the contract)`, and the stages on a line of their
        own past the preset's column when there are any.
    """
    head = f"  {action.name:<{width}}"
    if action.removed:
        return [f"{head}removed (by the contract)"]
    preset = "" if action.preset is None else f"{action.preset}  "
    mark = "on demand, " if action.on_demand else ""
    lines = [f"{head}{preset}({mark}{_SOURCE_TEXT[action.source]})"]
    if action.stages:
        lines.append(" " * (2 + width + 2) + ", ".join(action.stages))
    return lines


def _as_object(shown: ShownWork) -> dict[str, object]:
    """Describe a Work as plain data for JSON.

    Args:
        shown: The Work.

    Returns:
        The fields in the order of the contract, with `path` written with `/`.
        `roots` and `depends_on` are as written, and `resolved_roots` is the
        hierarchy's value, so it may differ from `roots` in order and repeats.
    """
    work = shown.work
    return {
        "id": work.id,
        "title": work.title,
        "path": work.path.as_posix(),
        "template": work.template,
        "parent": None if shown.parent is None else shown.parent.id,
        "roots": list(work.roots),
        "resolved_roots": list(shown.resolved_roots),
        "depends_on": list(work.depends_on),
        "dependents": [related.id for related in shown.dependents],
        "actions": [
            {
                "name": action.name,
                "source": action.source,
                "on_demand": action.on_demand,
                "preset": action.preset,
                "stages": list(action.stages),
            }
            for action in shown.actions
        ],
        "view": shown.view,
    }
