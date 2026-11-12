# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts list` prints."""

from typing import TYPE_CHECKING
lazy import json

from wio.contracts.discovery import discover_works
from wio.contracts.errors import ContractsError
from wio.contracts.hierarchy import build_hierarchy
lazy from wio.formats import render_text

_HINT = "`wio contracts check` shows every problem."
"""The line that a refusal ends with, so a person knows where to see them all."""
_NO_TITLE = "(no title)"

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Mapping

    from wio.contracts import Services
    from wio.contracts.discovery import WorkDiscovery
    from wio.contracts.hierarchy import Hierarchy
    from wio.io.ports import Stdio
    from wio.models.works import Work


def render_list(found: Hierarchy, *, as_json: bool) -> str:
    """Render the Works with their hierarchy for a person or for a program.

    It reads nothing and writes nothing. It imports `json` only for the JSON
    form.

    The human form has one block for each Work. Under `nesting` a Work comes
    before its children, each child is indented two spaces more than its parent,
    and siblings are in the order of their paths; under `flat` every Work is at
    the same indent, in the order of the paths. A block's first line is the id,
    padded to the widest id of the output, two spaces, the title or
    `(no title)`, and the template in brackets after two more spaces when the
    Work names one. The detail lines are indented to the title and each is
    written only when it has something to say: the path with `/`, always, then
    `roots:` as written and joined by `, `, then one `after: <id> <title>` for
    each dependency in the order listed, with `(no title)` for a Work that has
    none and `(not found)` for an id that no Work has, and `actions:` with each
    `name = value` of the Work's own `[actions]` in the order written, a stage
    preset bare, a list of stages in brackets joined by `, `, an empty list as
    `none`, the entries joined by `, `. Nothing is cut or wrapped.

    The JSON form is `json.dumps` of one array with its default separators, on
    one line, sorted by path alone, each object with `id`, `title`, `path`,
    `template`, `roots`, `depends_on`, `actions` and `parent` in that order:
    roots and dependencies as written, `title` and `template` `null` when there
    is none, `parent` the id of the parent or `null`, `actions` an object whose
    values are a string or an array, and `{}` when there is none.

    Args:
        found: The hierarchy of the Works, which has them sorted by path and the
            parent and children of each. The ids of its Works are not shared.
        as_json: Whether to render the array instead of the text.

    Returns:
        The text for standard output, ending in a newline, and empty for no Work
        in the human form, and `[]` and a newline in the JSON form.
    """
    if as_json:
        return json.dumps([_as_object(work, found) for work in found.works]) + "\n"
    order = _text_order(found)
    width = max((len(work.id) for work, _ in order), default=0)
    titles = {work.id: work.title for work in found.works}
    return "".join(
        f"{line}\n"
        for work, depth in order
        for line in _block(work, depth, width, titles)
    )


def _text_order(found: Hierarchy) -> list[tuple[Work, int]]:
    """Put the Works in the order of the text, each with its depth.

    Args:
        found: The hierarchy.

    Returns:
        Each Work after its parent and before the next sibling of its parent,
        siblings in the order of their paths, with the number of its ancestors.
        Under `flat` it is the Works in the order of their paths, all at 0.
    """
    order: list[tuple[Work, int]] = []
    pending = [
        (work, 0) for work in reversed(found.works) if not found.ancestors[work.path]
    ]
    while pending:
        work, depth = pending.pop()
        order.append((work, depth))
        pending.extend((kid, depth + 1) for kid in reversed(found.children[work.path]))
    return order


def _block(
    work: Work, depth: int, width: int, titles: Mapping[str, str | None]
) -> list[str]:
    """Lay out the lines of one Work.

    Args:
        work: The Work.
        depth: How many ancestors it has, each of which indents by two spaces.
        width: The widest id of the output, which the id is padded to.
        titles: The title of each Work by id, `None` for a Work with no title,
            and no key for an id that no Work has.

    Returns:
        The first line and the detail lines, none of them ended by a newline.
    """
    indent = "  " * depth
    template = f"  [{work.template}]" if work.template else ""
    first = f"{indent}{work.id.ljust(width)}  {work.title or _NO_TITLE}{template}"
    details = [work.path.as_posix()]
    if work.roots:
        details.append("roots: " + ", ".join(work.roots))
    details.extend(f"after: {_dependency(id_, titles)}" for id_ in work.depends_on)
    if work.actions:
        entries = (f"{name} = {_value(value)}" for name, value in work.actions.items())
        details.append("actions: " + ", ".join(entries))
    pad = indent + " " * (width + 2)
    return [first, *(pad + line for line in details)]


def _dependency(work_id: str, titles: Mapping[str, str | None]) -> str:
    """Write a dependency with the title of the Work it names.

    Args:
        work_id: The id as listed.
        titles: The title of each Work by id.

    Returns:
        The id and its title, `(no title)` for a Work with none, and `(not found)`
        for an id that no Work has.
    """
    if work_id not in titles:
        return f"{work_id} (not found)"
    return f"{work_id} {titles[work_id] or _NO_TITLE}"


def _value(value: str | tuple[str, ...]) -> str:
    """Write what an `[actions]` entry says.

    Args:
        value: A stage preset, or the stages of an action.

    Returns:
        The preset bare, the stages in brackets joined by `, `, and `none` for no
        stage.
    """
    if isinstance(value, str):
        return value
    return "[" + ", ".join(value) + "]" if value else "none"


def _as_object(work: Work, found: Hierarchy) -> dict[str, object]:
    """Describe a Work as plain data for JSON.

    Args:
        work: The Work.
        found: The hierarchy, for its parent.

    Returns:
        The fields in the order `render_list` gives, with the path written with
        `/`.
    """
    parent = found.parent[work.path]
    return {
        "id": work.id,
        "title": work.title,
        "path": work.path.as_posix(),
        "template": work.template,
        "roots": list(work.roots),
        "depends_on": list(work.depends_on),
        "actions": {
            name: value if isinstance(value, str) else list(value)
            for name, value in work.actions.items()
        },
        "parent": parent.id if parent else None,
    }


def run_list(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio contracts list`.

    It finds the Works, refuses a tree that is incomplete and prints them. It
    reads through `services` and writes only to `stdio.stdout`. A tree with an
    error that leaves it incomplete or ambiguous, a Work left out, a shared id, a
    collision or a Works directory that cannot be walked, lists nothing in either
    form. A wrong type of an optional key, an undeclared root, an unknown
    dependency and a cycle do not stop it.

    Args:
        services: What the command reads the project through.
        args: What the parser read: `json`, whether to write the array.
        stdio: Where the output goes.

    Returns:
        0 after the listing, which is empty for a tree with no Work.

    Raises:
        ContractsError: The tree is incomplete or ambiguous. It carries those
            errors, and its message is each rendered as
            `error: <where>: <message>` on a line of its own, then the line
            "`wio contracts check` shows every problem.". The command line
            writes the message as it is, with no prefix of its own, to standard
            error and exits 2.
        ConfigurationError: The config has an error.
    """
    config = services.settings.load()
    discovery = discover_works(services.repository.root(), config.works, services.files)
    _refuse_incomplete(discovery)
    found = build_hierarchy(discovery.works, config.works.hierarchy)
    stdio.stdout.write(render_list(found, as_json=args.json))
    return 0


def _refuse_incomplete(discovery: WorkDiscovery) -> None:
    """Refuse a tree that may not hold every Work, or whose ids are shared.

    Args:
        discovery: What one walk of the Works directory found.

    Raises:
        ContractsError: `incomplete` or `ambiguous` holds an error. It carries
            those errors in the order of `diagnostics`, and its message is them
            rendered one to a line and the hint.
    """
    left = {*discovery.incomplete, *discovery.ambiguous}
    refused = [error for error in discovery.diagnostics if error in left]
    if refused:
        message = f"{render_text(refused, keep_order=True)}\n{_HINT}"
        raise ContractsError(message, refused)
