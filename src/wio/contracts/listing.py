# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts list` prints."""

from typing import TYPE_CHECKING
lazy import json

from wio.contracts.discovery import discover_works
from wio.contracts.hierarchy import build_hierarchy

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
    raise NotImplementedError


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
    raise NotImplementedError


def _as_object(work: Work, found: Hierarchy) -> dict[str, object]:
    """Describe a Work as plain data for JSON.

    Args:
        work: The Work.
        found: The hierarchy, for its parent.

    Returns:
        The fields in the order `render_list` gives, with the path written with
        `/`.
    """
    raise NotImplementedError


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
    raise NotImplementedError
