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
    r"""Render a Work for a person or for a program.

    It reads nothing and writes nothing, and imports `json` only for the JSON
    form. The text and the JSON say the same facts, and the text ends in one line
    ending, at the `----` line when the view is empty.

    Args:
        shown: The Work with what `gather_work` found.
        as_json: Whether to render the object instead of the text.

    Returns:
        The text for standard output, or the JSON object on one line, ending in
        one line ending.

    Example:
        A Work with a parent and a dependency, whose actions are one from its
        template, one of its own and one that it removed:

            Work w4k7mn  Cache
              Path         .agents/wio/works/search/cache/README.md
              Template     feature.leaf
              Parent       q8d3zt  Search
              Roots        wio
              After        r2v6hc  Index

            Actions
              plan      plan-feature  (from the template)
                          plan, review-plan
              release   (from the contract)
                          tag, publish
              rollback  removed (by the contract)

            ----

            # Cache

            ## Purpose

            Keep what was read.

        A fact with nothing to say is left out, a second value goes on its own
        line in the column of the first, and `@descendants` shows what it
        resolves to, or `none`:

              Roots        e2e, @descendants → api, e2e
              After        r2v6hc  Twin
                           n5p7qr  (no title)
                           y4k2mq  (not found)
              Needed by    k3m9xq  Child

        An on-demand action, and a preset that the config does not declare, which
        has no stages line:

            Actions
              amend   amend-contract  (on demand, from the config defaults)
                        amend, review-amendment
              ratify  unknown  (from the config defaults)

        A Work that resolves to no action:

            Actions
              none

        The JSON of the first Work is one line with these fields in this order,
        `null` where there is none, and a removed action with its source and no
        preset or stages:

            {
              "id": "w4k7mn",
              "title": "Cache",
              "path": ".agents/wio/works/search/cache/README.md",
              "template": "feature.leaf",
              "parent": "q8d3zt",
              "roots": ["wio"],
              "resolved_roots": ["wio"],
              "depends_on": ["r2v6hc"],
              "dependents": [],
              "actions": [
                {"name": "rollback", "source": "contract", "on_demand": false,
                 "preset": null, "stages": []}
              ],
              "view": "# Cache\n\n## Purpose\n\nKeep what was read.\n"
            }
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
