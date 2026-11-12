# SPDX-License-Identifier: Apache-2.0
"""Creating a Work: what `wio contracts new` decides, writes and reports."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path

    from wio.contracts import Services
    from wio.contracts.discovery import WorkDiscovery
    from wio.contracts.location import IdGenerator, NameArguments
    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem, Stdio
    from wio.models.config import Config


@dataclass(frozen=True)
class NewArguments:
    """What was typed after `wio contracts new`, as it was typed.

    Provisional: the field names may change. It is immutable.

    Attributes:
        kind: The kind, whose entry template the Work starts from, or `None`.
        template: The `--template`, which the Work starts from, or `None`.
        name: The options that name the Work and say where it goes.
        roots: The `--root` names in the order given, a name that was given twice
            included.
    """

    kind: str | None
    template: str | None
    name: NameArguments
    roots: tuple[str, ...]


@dataclass(frozen=True)
class NewWork:
    """A Work that is decided and not yet written.

    It is immutable.

    Attributes:
        id: The new Work's id.
        title: The text of the first level-1 heading of `text`, or `None` when it
            has none.
        path: The file, relative to the repository root.
        template: The name of the template it follows, or `None` for a bare
            contract.
        parent: The id of its parent in the tree, or `None`.
        text: The whole file, ending as the skeleton does.
    """

    id: str
    title: str | None
    path: Path
    template: str | None
    parent: str | None
    text: str


def plan_work(
    arguments: NewArguments,
    config: Config,
    discovery: WorkDiscovery,
    catalog: TemplateCatalog,
    files: FileSystem,
    root: Path,
    generator: IdGenerator,
) -> NewWork:
    """Decide the new Work and write nothing.

    Everything that was asked for is checked before anything is decided about the
    file, and there is one error for each call, the first of these: no kind is
    declared for `new <kind>`, the kind is not declared, the template is missing or
    rejected or is of another kind than the kind, a root is not declared, the title
    is not one non-blank line, which is ``The title must be one non-blank line``,
    then the errors of `decide_place`. The messages say
    what to do: a template that is rejected, or is the entry template of a kind,
    points to `wio templates check`, and a name that no file has points to
    `wio templates list`.

    The template is the entry template of the kind, `--template`'s, or none for a
    bare contract; given both a kind and `--template`, its kind must be the kind.
    The text is `prepare_skeleton`'s of the template's file, which is read at the
    catalog's path, or `<!-- wio`, `-->`, an empty line and `# Title` for a bare
    contract. On it `set_block_keys` adds the `id` first, and `roots` replaced or
    added when `--root` was given, a name given twice counting once in the order of
    its first appearance and each name a declared root or `@descendants`. The first
    level-1 heading is found by `read_outline` of the body and its first line,
    which `read_metadata_block` gives for the text. A title is trimmed and replaces
    that heading, or is inserted before the first
    line of the body that is not empty and followed by one empty line, in the
    template's line ending, or at the end of the body when it has no such line.
    Nothing else of the skeleton changes. The parent is `parent_of` in
    `wio.contracts.hierarchy` of the new file's path, the one definition of the
    rule, whether the place came from `--parent` or from `--path`, and none under
    `flat`. An undeclared root is the error ``The root `r` is not declared in
    `[roots]` of the config``, as the check of the Works words it. `set_block_keys`
    is called by its name in this module, once, with the `id` and, when roots were
    given, `roots`.

    Args:
        arguments: What was typed.
        config: The settings, which declare the kinds, their entry templates and the
            roots, and the hierarchy mode.
        discovery: The Works found, for the id, the parent and the place.
        catalog: Finds a template and says whether `wio templates check` rejects it.
        files: Reads the template's text and tells what exists.
        root: The repository root.
        generator: Draws the candidate ids.

    Returns:
        The Work, with its text and its place.

    Raises:
        ContractsError: One of the mistakes above, or one of `decide_place` and
            `new_id`.
    """
    raise NotImplementedError


def render_report(work: NewWork, *, as_json: bool) -> str:
    """Write what `new` says of a Work that was written.

    Args:
        work: The Work.
        as_json: Whether to write one JSON object instead of the text.

    Returns:
        The human form, `Created Work <id>  <title>` and the path on the next line
        indented by two spaces, with `(no title)` for a Work with none, or one JSON
        object on one line with `id`, `title`, `path`, `template` and `parent` in
        that order, `null` for none, and the path written with `/`. It ends in a
        newline and imports `json` only for the JSON form.
    """
    raise NotImplementedError


def run_new(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio contracts new`.

    It loads the config, finds the Works, plans the Work, writes its one file
    through the guard and reports. Everything is checked before the write, so a
    mistake creates nothing, and the report follows the write, so a write that
    fails reports nothing on standard output.

    Args:
        services: What the command reads and writes the project through.
        args: What the parser read: `kind`, `template`, `parent`, `slug`, `title`,
            `path`, `root` and `json`.
        stdio: Where the report goes.

    Returns:
        0 after the Work is written.

    Raises:
        ContractsError: A mistake of the user, or a file that exists, which the
            command line reports and exits 2 for.
        ConfigurationError: The config has an error.
    """
    raise NotImplementedError
