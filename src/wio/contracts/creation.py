# SPDX-License-Identifier: Apache-2.0
"""Creating a Work: what `wio contracts new` decides, writes and reports."""

import re
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
from wio.contracts.roots import undeclared_root
from wio.formats import (
    encode_json,
    prepare_skeleton,
    read_metadata_block,
    read_outline,
    set_block_keys,
)
from wio.formats.markdown import parse
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
    """Plan a new Work without writing a file.

    Choose the requested template, the kind's entry template, or none for a
    bare contract. A template used with a kind must have that kind. Validate
    the template, roots and title before deciding the place: report the first
    error in that order, followed by errors from `decide_place`. A rejected template or
    missing entry template points to `wio templates check`; another unknown
    template name points to `wio templates list`.

    Build the text from the template's skeleton or a bare metadata block and
    `# Title`. Add the new id and, if requested, replace the roots with declared
    roots or `@descendants`, deduplicated in first-seen order. Preserve the
    other metadata values and skeleton, except for TOML comments in the block.
    A supplied title must be one non-blank line; trim it and replace the first
    level-1 heading, or insert it before the first non-empty body line (or at
    the end), followed by an empty line in the template's line ending.
    Determine the parent from the chosen path using `parent_of`; under `flat`
    there is none.

    Args:
        arguments: The requested kind, template, roots, title and place.
        config: The declared kinds, roots and hierarchy mode.
        discovery: The existing Works.
        catalog: Finds templates and reports whether they are rejected.
        files: Reads templates and checks paths.
        root: The repository root.
        generator: Draws candidate ids.

    Returns:
        The planned Work, including its text and place.

    Raises:
        ContractsError: An invalid request or an error from `decide_place` or
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
    """Select a usable template, refusing a kind or template mistake."""
    name = _template_name(arguments, config)
    if name is None:
        return None
    template = find_template(name, catalog, entry=arguments.template is None)
    if arguments.kind is not None and template.kind != arguments.kind:
        msg = (
            f"The template `{name}` is of kind `{template.kind}`, "
            f"not `{arguments.kind}`"
        )
        raise ContractsError(msg)
    return template


def _template_name(arguments: NewArguments, config: Config) -> str | None:
    """Validate the requested kind and find the requested template name."""
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


def find_template(name: str, catalog: TemplateCatalog, *, entry: bool) -> Template:
    """Find a template and refuse a missing or rejected one.

    `wio contracts new` and `wio contracts skeleton` find their template with it,
    so they refuse the same way. A rejected template is reported before a missing
    one.

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
    """Check root names and retain their first appearances."""
    for root in roots:
        if undeclared_root(root, config.roots):
            msg = f"The root `{root}` is not declared in `[roots]` of the config"
            raise ContractsError(msg)
    return tuple(dict.fromkeys(roots))


def _validate_title(title: str | None) -> str | None:
    """Trim a title or refuse one that is blank or spans lines."""
    if title is None:
        return None
    trimmed = title.strip()
    if not trimmed or "\n" in trimmed or "\r" in trimmed:
        msg = "The title must be one non-blank line"
        raise ContractsError(msg)
    return trimmed


def _set_title(text: str, title: str) -> str:
    """Replace the first level-one heading or insert one in the body."""
    block = read_metadata_block(text)
    assert block is not None
    prefix = text[: -len(block.body)] if block.body else text
    lines = re.findall(r"[^\r\n]*(?:\r\n|\r|\n|$)", block.body)
    if lines and not lines[-1]:
        lines.pop()
    heading = _first_title(block.body, block.body_start_line)
    ending = "\r\n" if text.split("\n", 1)[0].endswith("\r") else "\n"
    if heading is not None:
        index = heading.line - block.body_start_line
        line = lines[index]
        suffix = _line_ending(line)
        comments = _heading_comments(line)
        lines[index] = _render_heading(title, comments) + suffix
    else:
        _insert_title(lines, title, ending, text)
    return prefix + "".join(lines)


def _heading_comments(line: str) -> list[str]:
    """Find real inline HTML comments in a Markdown heading."""
    marker = " wio-comment-boundary"
    while marker in line:
        marker += "-"
    terminator = marker + "-->"
    probe = line.removesuffix(_line_ending(line)) + terminator
    return [
        child.content.removesuffix(terminator)
        for token in parse(probe)
        for child in token.children or ()
        if child.type == "html_inline" and child.content.startswith("<!--")
    ]


def _insert_title(lines: list[str], title: str, ending: str, text: str) -> None:
    """Insert a title before the first nonempty body line."""
    index = next((i for i, line in enumerate(lines) if line.strip()), len(lines))
    if index and not _line_ending(lines[index - 1]):
        lines[index - 1] += ending
    suffix = ending * 2 if index < len(lines) else _final_endings(text)
    lines.insert(index, f"# {_heading_title(title)}{suffix}")


def _final_endings(text: str) -> str:
    """Return the sequence of line endings at the end of text."""
    match = re.search(r"(?:(?:\r\n|\n|\r))+$", text)
    return match.group() if match else ""


def _heading_title(title: str) -> str:
    """Protect a title's final hashes from Markdown's closing heading syntax."""
    prefix = title.rstrip("#")
    if title.endswith("#") and (not prefix or prefix[-1].isspace()):
        return title + " #"
    return title


def _render_heading(title: str, comments: list[str]) -> str:
    """Write the heading title and any preserved authoring comments."""
    if comments:
        return f"# {title} {' '.join(comments)}"
    return f"# {_heading_title(title)}"


def _first_title(body: str, start: int) -> Heading | None:
    """Find the first level-one heading of the body."""
    return next((h for h in read_outline(body, start) if h.level == 1), None)


def _line_ending(line: str) -> str:
    """Return a line's CRLF, LF or absent ending."""
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    return "\r" if line.endswith("\r") else ""


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
        return (
            encode_json(
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
