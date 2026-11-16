# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts show` writes, as text or as JSON."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.contracts.showing import ShownWork


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
    the contract)` with no mark, although the JSON keeps the config's flag.

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
    raise NotImplementedError
