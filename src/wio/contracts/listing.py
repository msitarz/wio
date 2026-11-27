# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts list` prints."""

from typing import TYPE_CHECKING

from wio.contracts.discovery import discover_works
from wio.contracts.hierarchy import build_hierarchy
from wio.contracts.refusal import refuse_tree
lazy from wio.formats import Block, encode_json, render_blocks

_NO_TITLE = "(no title)"

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Mapping

    from wio.contracts import Services
    from wio.contracts.hierarchy import Hierarchy
    from wio.io.ports import Stdio
    from wio.models.works import Work


def render_list(found: Hierarchy, *, as_json: bool) -> str:
    """Render the Works with their hierarchy for a person or for a program."""
    if as_json:
        return encode_json([_as_object(work, found) for work in found.works]) + "\n"
    titles = {work.id: work.title for work in found.works}
    return render_blocks(
        [_block(work, depth, titles) for work, depth in _text_order(found)]
    )


def _text_order(found: Hierarchy) -> list[tuple[Work, int]]:
    """Put the Works in the order of the text, each with its depth."""
    order: list[tuple[Work, int]] = []
    pending = [
        (work, 0) for work in reversed(found.works) if not found.ancestors[work.path]
    ]
    while pending:
        work, depth = pending.pop()
        order.append((work, depth))
        pending.extend((kid, depth + 1) for kid in reversed(found.children[work.path]))
    return order


def _block(work: Work, depth: int, titles: Mapping[str, str | None]) -> Block:
    """Describe one Work as a block of the listing."""
    details = [work.path.as_posix()]
    if work.roots:
        details.append("roots: " + ", ".join(work.roots))
    details.extend(f"after: {_dependency(id_, titles)}" for id_ in work.depends_on)
    if work.actions:
        entries = (f"{name} = {_value(value)}" for name, value in work.actions.items())
        details.append("actions: " + ", ".join(entries))
    suffix = f"[{work.template}]" if work.template else None
    return Block(depth, work.id, work.title or _NO_TITLE, suffix, tuple(details))


def _dependency(work_id: str, titles: Mapping[str, str | None]) -> str:
    """Write a dependency with the title of the Work it names."""
    if work_id not in titles:
        return f"{work_id} (not found)"
    return f"{work_id} {titles[work_id] or _NO_TITLE}"


def _value(value: str | tuple[str, ...]) -> str:
    """Write what an `[actions]` entry says."""
    if isinstance(value, str):
        return value
    return "[" + ", ".join(value) + "]" if value else "none"


def _as_object(work: Work, found: Hierarchy) -> dict[str, object]:
    """Describe a Work as plain data for JSON."""
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
    refuse_tree(discovery, shared=True)
    found = build_hierarchy(discovery.works, config.works.hierarchy)
    stdio.stdout.write(render_list(found, as_json=args.json))
    return 0
