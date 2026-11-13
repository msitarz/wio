# SPDX-License-Identifier: Apache-2.0
"""Creating a Work: what `wio contracts new` decides, writes and reports."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.contracts.discovery import discover_works
from wio.contracts.errors import ContractsError
from wio.contracts.hierarchy import parent_of
from wio.contracts.location import (
    NameArguments,
    RandomIds,
    decide_place,
    new_id,
    write_new,
)
from wio.formats import (
    prepare_skeleton,
    read_metadata_block,
    read_outline,
    set_block_keys,
)
lazy from wio.models.template import Template

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path

    from wio.contracts import Services
    from wio.contracts.discovery import WorkDiscovery
    from wio.contracts.location import IdGenerator
    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem, Stdio
    from wio.models.config import Config
    from wio.models.heading import Heading


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
    contract. On it `set_block_keys` adds the `id`, and `roots` replaced or
    added when `--root` was given, a name given twice counting once in the order of
    its first appearance and each name a declared root or `@descendants`. The first
    level-1 heading is found by `read_outline` of the body and its first line,
    which `read_metadata_block` gives for the text. A title is trimmed and replaces
    that heading, or is inserted before the first
    line of the body that is not empty and followed by one empty line, in the
    template's line ending, or at the end of the body when it has no such line.
    The block's key placement and spacing may change, but its other values and
    comments and the rest of the skeleton are retained. The parent is `parent_of` in
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
    template = _choose_template(arguments, config, catalog)
    roots = _validate_roots(arguments.roots, config)
    title = _validate_title(arguments.name.title)
    path = decide_place(root, config.works, discovery, files, arguments.name)
    identifier = new_id(generator, discovery.works)
    text = (
        prepare_skeleton(template.name, files.read_text(root / template.path))
        if template is not None
        else "<!-- wio\n-->\n\n# Title\n"
    )
    keys: dict[str, object] = {"id": identifier}
    if roots:
        keys["roots"] = list(roots)
    text = set_block_keys(text, keys)
    if title is not None:
        text = _set_title(text, title)
    block = read_metadata_block(text)
    assert block is not None
    heading = _first_title(block.body, block.body_start_line)
    parent = parent_of(path, discovery.works, config.works.hierarchy)
    return NewWork(
        identifier,
        heading.text if heading else None,
        path,
        template.name if template else None,
        parent.id if parent else None,
        text,
    )


def _choose_template(
    arguments: NewArguments, config: Config, catalog: TemplateCatalog
) -> Template | None:
    """Select a usable template, refusing a kind or template mistake.

    Args:
        arguments: The requested kind and template.
        config: The declared kinds.
        catalog: The template catalog.

    Returns:
        The chosen template, or none for a bare Work.

    Raises:
        ContractsError: The kind or template cannot be used.
    """
    name = _template_name(arguments, config)
    if name is None:
        return None
    template = _find_template(name, catalog, entry=arguments.template is None)
    if arguments.kind is not None and template.kind != arguments.kind:
        msg = (
            f"The template `{name}` is of kind `{template.kind}`, "
            f"not `{arguments.kind}`"
        )
        raise ContractsError(msg)
    return template


def _template_name(arguments: NewArguments, config: Config) -> str | None:
    """Validate the requested kind and find the requested template name.

    Args:
        arguments: The requested kind and template.
        config: The declared kinds.

    Returns:
        The requested or entry template name, or none for a bare Work.

    Raises:
        ContractsError: The requested kind is not declared.
    """
    kinds, kind = config.templates.kinds, arguments.kind
    if kind is not None and not kinds:
        msg = "No kinds are declared in `[templates.kinds]` of the config"
        raise ContractsError(msg)
    if kind is not None and kind not in kinds:
        msg = f"The kind `{kind}` is not declared; declared kinds: {', '.join(kinds)}"
        raise ContractsError(msg)
    return (
        arguments.template
        if arguments.template is not None
        else (kinds[kind] if kind is not None else None)
    )


def _find_template(name: str, catalog: TemplateCatalog, *, entry: bool) -> Template:
    """Find a template and refuse a missing or rejected one.

    Args:
        name: The template name.
        catalog: The template catalog.
        entry: Whether the kind names this as its entry template.

    Returns:
        The usable template.

    Raises:
        ContractsError: The template is missing or rejected.
    """
    rejected = catalog.is_rejected(name)
    template = catalog.find(name)
    if rejected:
        msg = f"The template `{name}` is rejected; run `wio templates check`"
        raise ContractsError(msg)
    if template is None:
        hint = "wio templates check" if entry else "wio templates list"
        msg = f"The template `{name}` was not found; run `{hint}`"
        raise ContractsError(msg)
    return template


def _validate_roots(roots: tuple[str, ...], config: Config) -> tuple[str, ...]:
    """Check root names and retain their first appearances.

    Args:
        roots: The requested root names.
        config: The declared roots.

    Returns:
        The names, each once, in order of first appearance.

    Raises:
        ContractsError: A name is not declared.
    """
    for root in roots:
        if root != "@descendants" and root not in config.roots:
            msg = f"The root `{root}` is not declared in `[roots]` of the config"
            raise ContractsError(msg)
    return tuple(dict.fromkeys(roots))


def _validate_title(title: str | None) -> str | None:
    """Trim a title or refuse one that is blank or spans lines.

    Args:
        title: The requested title, or none.

    Returns:
        The trimmed title, or none.

    Raises:
        ContractsError: The title is blank or spans lines.
    """
    if title is None:
        return None
    trimmed = title.strip()
    if not trimmed or "\n" in title or "\r" in title:
        msg = "The title must be one non-blank line"
        raise ContractsError(msg)
    return trimmed


def _set_title(text: str, title: str) -> str:
    """Replace the first level-one heading or insert one in the body.

    Args:
        text: A contract with a metadata block.
        title: The validated title.

    Returns:
        The contract with its title set.
    """
    block = read_metadata_block(text)
    assert block is not None
    prefix = text[: -len(block.body)] if block.body else text
    lines = block.body.splitlines(keepends=True)
    heading = _first_title(block.body, block.body_start_line)
    ending = "\r\n" if text.split("\n", 1)[0].endswith("\r") else "\n"
    if heading is not None:
        index = heading.line - block.body_start_line
        line = lines[index]
        suffix = _line_ending(line)
        lines[index] = f"# {title}{suffix}"
    else:
        _insert_title(lines, title, ending)
    return prefix + "".join(lines)


def _insert_title(lines: list[str], title: str, ending: str) -> None:
    """Insert a title before the first nonempty body line.

    Args:
        lines: The body lines to update.
        title: The validated title.
        ending: The template's line ending.
    """
    index = next((i for i, line in enumerate(lines) if line.strip()), len(lines))
    if index and not _line_ending(lines[index - 1]):
        lines[index - 1] += ending
    lines.insert(index, f"# {title}{ending}" + (ending if index < len(lines) else ""))


def _first_title(body: str, start: int) -> Heading | None:
    """Find the first level-one heading of the body.

    Args:
        body: The body to inspect.
        start: Its first line number in the file.

    Returns:
        The first level-one heading, or none.
    """
    return next((h for h in read_outline(body, start) if h.level == 1), None)


def _line_ending(line: str) -> str:
    """Return a line's CRLF, LF or absent ending.

    Args:
        line: The line, including any ending.

    Returns:
        Its line ending, or an empty string.
    """
    if line.endswith("\r\n"):
        return "\r\n"
    return "\n" if line.endswith("\n") else ""


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
    if as_json:
        import json

        return (
            json.dumps(
                {
                    "id": work.id,
                    "title": work.title,
                    "path": work.path.as_posix(),
                    "template": work.template,
                    "parent": work.parent,
                }
            )
            + "\n"
        )
    title = work.title or "(no title)"
    return f"Created Work {work.id}  {title}\n  {work.path.as_posix()}\n"


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
    config = services.settings.load()
    root = services.repository.root()
    discovery = discover_works(root, config.works, services.files)
    name = NameArguments(args.slug, args.title, args.path, args.parent)
    arguments = NewArguments(args.kind, args.template, name, tuple(args.root))
    work = plan_work(
        arguments,
        config,
        discovery,
        services.catalog,
        services.files,
        root,
        RandomIds(services.entropy),
    )
    write_new(services.files, root, work.path, work.text)
    stdio.stdout.write(render_report(work, as_json=args.json))
    return 0
