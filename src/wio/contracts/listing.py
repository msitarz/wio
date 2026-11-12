# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts list` prints."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

    from wio.contracts import Services
    from wio.contracts.hierarchy import Hierarchy
    from wio.io.ports import Stdio


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
        ContractsError: The tree is incomplete or ambiguous. The message is each
            such error as `error: <where>: <message>` on a line of its own,
            then the line "`wio contracts check` shows every problem.". The
            command line exits 2 and writes it to standard error.
        ConfigurationError: The config has an error.
    """
    raise NotImplementedError
