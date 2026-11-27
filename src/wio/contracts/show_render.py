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
    """Render a Work as human-readable text or one-line JSON.

    Pure formatter (no I/O); output always ends with a single newline.

    Args:
        shown: The Work gathered by `gather_work`.
        as_json: Render a single-line JSON object instead of text.

    Example:
        Text output layout::

            Work w4k7mn  Cache
              Path      .agents/wio/works/search/cache/README.md
              Template  feature.leaf
              Roots     wio

            Actions
              plan  plan-feature  (from the template)
                      plan, review-plan

            ----

            # Cache
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
    """Write the first line of the text."""
    work = shown.work
    return f"Work {work.id}  {_NO_TITLE if work.title is None else work.title}"


def _fact_lines(shown: ShownWork) -> list[str]:
    """Write the fact lines of the text."""
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
    """Lay out the values of one fact under its label."""
    return [
        f"  {label if index == 0 else '':<{_LABEL_WIDTH}}{value}"
        for index, value in enumerate(values)
    ]


def _related(related: Related) -> str:
    """Write a related Work as `<id> <title>`."""
    if not related.found:
        return f"{related.id}  {_NOT_FOUND}"
    return f"{related.id}  {_NO_TITLE if related.title is None else related.title}"


def _roots(shown: ShownWork) -> list[str]:
    """Write the roots of a Work."""
    roots = shown.work.roots
    if not roots:
        return []
    text = ", ".join(roots)
    if _DESCENDANTS in roots:
        text += f" \u2192 {', '.join(shown.resolved_roots) or 'none'}"
    return [text]


def _action_lines(actions: Sequence[ShownAction]) -> list[str]:
    """Write the lines of the actions block."""
    if not actions:
        return ["  none"]
    width = max(len(action.name) for action in actions) + 2
    return [line for action in actions for line in _action(action, width)]


def _action(action: ShownAction, width: int) -> list[str]:
    """Write one action and its stages."""
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
    """Describe a Work as plain data for JSON."""
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
