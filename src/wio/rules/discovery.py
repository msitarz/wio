# SPDX-License-Identifier: Apache-2.0
"""Finding the rulesets of a repository and reading their manifests and rules."""

from dataclasses import dataclass
from functools import partial
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from wio.errors import DiagnosticsError
from wio.formats.errors import MetadataBlockError
from wio.formats.grammar import NAME, NAME_FORM
from wio.io.walk import refuse_directory
from wio.models.diagnostics import Diagnostic, has_error, sort_diagnostics
from wio.models.rule import LoadedRuleset, Manifest
from wio.rules.manifest import read_manifest
from wio.rules.reading import read_rule
lazy from wio.formats import read_metadata_block
lazy from wio.formats.diagnostics import render_text

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.rule import Rule

_RULES = ".agents/wio/rules"
_MANIFEST = "ruleset.toml"
_SUFFIX = ".md"
_error = partial(Diagnostic, "error")
"""Make an error diagnostic from a place and a message."""


@dataclass(frozen=True)
class Discovery:
    """What one walk of `.agents/wio/rules` found.

    Attributes:
        rulesets: The rulesets that were read whole, sorted by name. A ruleset
            whose directory, manifest or name is at fault is left out, and the
            others are still here.
        diagnostics: Every error and warning found, in the order of
            `sort_diagnostics`, whatever the order in which the port lists the
            files and directories.
    """

    rulesets: tuple[LoadedRuleset, ...]
    diagnostics: tuple[Diagnostic, ...]


def discover(root: Path, files: FileSystem) -> Discovery:
    """Walk `.agents/wio/rules` and read each ruleset.

    It reads files only through `files` and writes none. A ruleset is a
    directory directly under `.agents/wio/rules` whose name has the form of a
    ruleset name, with a `ruleset.toml`; it holds the rules of the Markdown files
    below it that `read_rule` takes for rules. Hidden directories are not
    entered. The rulesets are judged against their own manifests: a rule of a
    family the manifest does not declare, and rules that share a code or a name
    within a ruleset, are errors and leave those rules out, while the same code
    in two rulesets is no fault.

    Faults are errors, and everything else is still read; nothing is raised for
    a fault of the files. Each names its place, written with `/` and relative to
    `root`:

    - the file, followed by `:<line>` when the fault has a line, for a rule file
      that cannot be read, decoded or parsed, a rule of a family that its
      manifest does not declare, a `ruleset.toml` that is a symbolic link, one
      below a ruleset's directory, and a marked rule file directly in
      `.agents/wio/rules`, whose block that cannot be read is that fault, with
      its line;
    - the manifest followed by `#` and the key path for a key of a manifest,
      by `:<line>` for a manifest that does not parse, and alone for one that
      cannot be read or decoded;
    - the two files joined by `, `, written in order, for a code or a name that
      two rules of one ruleset share;
    - the directory for a fault of a directory: `.agents/wio/rules` that is a
      symbolic link, not a directory or cannot be listed, and a ruleset
      directory that is a symbolic link, has a name of the wrong form, has no
      `ruleset.toml` or cannot be listed.

    A missing rules directory is no fault. The warnings of `read_manifest` and
    `read_rule` are returned with the errors. A ruleset whose rules are at fault
    is still returned without those rules, and one whose directory, manifest or
    name is at fault is left out. A file directly in `.agents/wio/rules` is a
    stray rule file when `read_metadata_block` finds a block in it, and is
    ignored otherwise. The rules of a ruleset are in the order of family, then
    the number of the code, then the text of the code.

    Args:
        root: The repository root.
        files: The port that lists directories and reads files.

    Returns:
        The rulesets and the diagnostics.
    """
    entries, found = _list_rules_directory(root, files)
    rulesets: list[LoadedRuleset] = []
    for entry in entries:
        ruleset, diagnostics = _read_entry(root, entry, files)
        rulesets.extend(ruleset)
        found.extend(diagnostics)
    ordered = sorted(rulesets, key=lambda ruleset: ruleset.name)
    return Discovery(tuple(ordered), sort_diagnostics(found))


def _list_rules_directory(
    root: Path, files: FileSystem
) -> tuple[list[Path], list[Diagnostic]]:
    """List the entries of `.agents/wio/rules`, unless it must not be walked.

    Args:
        root: The repository root.
        files: The port that lists directories.

    Returns:
        The entries in the order of their names, none for a rules directory that
        is missing, which is no fault, that is a symbolic link or not a
        directory, or that cannot be listed, the last three with one error.
    """
    directory = root / _RULES
    refusal = refuse_directory(directory, _RULES, files, noun="rules", default=_RULES)
    if refusal is not None:
        return [], list(refusal)
    if not files.is_dir(directory):
        return [], []
    try:
        return sorted(files.list_dir(directory)), []
    except OSError as error:
        return [], [_unlistable(_RULES, error)]


def refuse_on_errors(discovery: Discovery) -> None:
    """Refuse a discovery that has an error.

    Args:
        discovery: What `discover` returned.

    Raises:
        DiagnosticsError: The discovery holds an error. It carries the error
            diagnostics, in order, and not the warnings.
    """
    if not has_error(discovery.diagnostics):
        return
    errors = tuple(d for d in discovery.diagnostics if d.severity == "error")
    raise DiagnosticsError(render_text(errors, keep_order=True), errors)


def _place(root: Path, path: Path) -> str:
    """Write the place of a path.

    Args:
        root: The repository root.
        path: A file or directory below it.

    Returns:
        The path relative to the root, written with `/`.
    """
    return path.relative_to(root).as_posix()


def _unlistable(place: str, error: OSError) -> Diagnostic:
    """Make the error of a directory that cannot be listed.

    Args:
        place: The directory's place.
        error: What the port raised.

    Returns:
        The error.
    """
    return _error(place, f"The directory cannot be listed: {error.strerror}")


def _read_entry(
    root: Path, entry: Path, files: FileSystem
) -> tuple[list[LoadedRuleset], list[Diagnostic]]:
    """Judge one entry directly under the rules directory.

    Args:
        root: The repository root.
        entry: The entry.
        files: The port that reads the files.

    Returns:
        The ruleset as a list of one, none when the entry is not a ruleset or is
        at fault, and what was found.
    """
    place = _place(root, entry)
    if files.is_symlink(entry):
        if not files.is_dir(entry):
            return [], []
        return [], [_error(place, "A ruleset must not be a symbolic link")]
    if not files.is_dir(entry):
        return [], _stray(root, entry, files)
    if entry.name.startswith("."):
        return [], []
    if not NAME.fullmatch(entry.name):
        message = (
            f"`{entry.name}` is not a ruleset name; a ruleset name is {NAME_FORM}."
        )
        return [], [_error(place, message)]
    ruleset, diagnostics = _read_ruleset(root, entry, files)
    return ([ruleset] if ruleset else []), diagnostics


def _stray(root: Path, entry: Path, files: FileSystem) -> list[Diagnostic]:
    """Judge a file directly under the rules directory.

    Args:
        root: The repository root.
        entry: The file.
        files: The port that reads it.

    Returns:
        An error when it is a Markdown file that holds a metadata block, which
        would be a rule file outside any ruleset, or whose block cannot be read;
        none for any other file.
    """
    if not entry.name.endswith(_SUFFIX):
        return []
    place = _place(root, entry)
    try:
        block = read_metadata_block(files.read_text(entry))
    except UnicodeDecodeError:
        return [_error(place, "The file is not valid UTF-8")]
    except OSError as error:
        return [_error(place, f"The file cannot be read: {error.strerror}")]
    except MetadataBlockError as error:
        return [_error(f"{place}:{error.line}", error.message)]
    if block is None:
        return []
    message = "A rule file must be in the directory of a ruleset, not directly here"
    return [_error(place, message)]


def _read_ruleset(
    root: Path, directory: Path, files: FileSystem
) -> tuple[LoadedRuleset | None, list[Diagnostic]]:
    """Read the manifest and the rules of one ruleset directory.

    Args:
        root: The repository root.
        directory: The ruleset's directory, whose name has a ruleset name's form.
        files: The port that lists and reads.

    Returns:
        The ruleset, or `None` when its directory, its manifest or its name is at
        fault, and everything found, warnings included.
    """
    place = _place(root, directory)
    manifest, found = _read_manifest(root, directory, files)
    try:
        paths = list(_walk(directory, files))
    except OSError as error:
        return None, [*found, _unlistable(place, error)]
    found.extend(_nested_manifests(root, directory, paths))
    if manifest is None:
        return None, found
    markdown = sorted(p for p in paths if p.name.endswith(_SUFFIX))
    rules, problems = _read_rules(root, directory.name, markdown, files)
    kept, relations = _relate(rules, manifest)
    ruleset = LoadedRuleset(directory.name, PurePosixPath(place), manifest, tuple(kept))
    return ruleset, [*found, *problems, *relations]


def _nested_manifests(
    root: Path, directory: Path, paths: list[Path]
) -> list[Diagnostic]:
    """Find the manifests below a ruleset's directory, which are never read.

    Args:
        root: The repository root.
        directory: The ruleset's directory.
        paths: The files below it.

    Returns:
        An error for each `ruleset.toml` that is not directly in the directory.
    """
    message = "A manifest is not read below a ruleset's directory"
    return [
        _error(_place(root, path), message)
        for path in paths
        if path.name == _MANIFEST and path.parent != directory
    ]


def _read_manifest(
    root: Path, directory: Path, files: FileSystem
) -> tuple[Manifest | None, list[Diagnostic]]:
    """Read the `ruleset.toml` of a ruleset directory.

    Args:
        root: The repository root.
        directory: The ruleset's directory.
        files: The port that reads the file.

    Returns:
        The manifest, or `None` with an error when the file is missing, is a
        symbolic link, cannot be read or decoded, or has an error; with the
        warnings and errors that `read_manifest` reported.
    """
    path = directory / _MANIFEST
    place = _place(root, path)
    if files.is_symlink(path):
        return None, [_error(place, "A manifest must not be a symbolic link")]
    if not files.exists(path):
        message = f"The ruleset has no `{_MANIFEST}`"
        return None, [_error(_place(root, directory), message)]
    try:
        text = files.read_text(path)
    except UnicodeDecodeError:
        return None, [_error(place, "The file is not valid UTF-8")]
    except OSError as error:
        return None, [_error(place, f"The file cannot be read: {error.strerror}")]
    reading = read_manifest(PurePosixPath(place), text)
    return reading.manifest, list(reading.diagnostics)


def _walk(directory: Path, files: FileSystem) -> Iterator[Path]:
    """List the files below a ruleset's directory, whatever their names.

    Args:
        directory: The directory to walk.
        files: The port that lists directories.

    Yields:
        Each file, skipping symbolic links and directories whose names start
        with `.` and anything below them.

    Raises:
        OSError: A directory cannot be listed.
    """
    for entry in files.list_dir(directory):
        if files.is_symlink(entry):
            continue
        if not files.is_dir(entry):
            yield entry
        elif not entry.name.startswith("."):
            yield from _walk(entry, files)


def _read_rules(
    root: Path, ruleset: str, paths: list[Path], files: FileSystem
) -> tuple[list[Rule], list[Diagnostic]]:
    """Read the Markdown files of a ruleset that are rules.

    Args:
        root: The repository root.
        ruleset: The name of the ruleset.
        paths: Its Markdown files.
        files: The port that reads them.

    Returns:
        The rules read, and the errors and warnings of the files.
    """
    rules: list[Rule] = []
    found: list[Diagnostic] = []
    for path in paths:
        place = _place(root, path)
        try:
            text = files.read_text(path)
        except UnicodeDecodeError:
            found.append(_error(place, "The file is not valid UTF-8"))
            continue
        except OSError as error:
            found.append(_error(place, f"The file cannot be read: {error.strerror}"))
            continue
        reading = read_rule(ruleset, PurePosixPath(place), text)
        found.extend(reading.diagnostics)
        if reading.rule is not None:
            rules.append(reading.rule)
    return rules, found


def _relate(
    rules: list[Rule], manifest: Manifest
) -> tuple[list[Rule], list[Diagnostic]]:
    """Judge the rules of one ruleset against its manifest and each other.

    Args:
        rules: The rules of the ruleset.
        manifest: Its manifest.

    Returns:
        The rules in the order of family, number and code text, without those of
        an undeclared family and those that share a code or a name, and one
        error for each such fault.
    """
    found: list[Diagnostic] = []
    declared: list[Rule] = []
    for rule in rules:
        if rule.family in manifest.families:
            declared.append(rule)
            continue
        message = f"The family `{rule.family}` is not declared in `{_MANIFEST}`"
        found.append(_error(rule.path.as_posix(), message))
    unique, by_code = _unshared(declared, lambda r: r.code, "the code")
    unique, by_name = _unshared(unique, lambda r: r.name, "the name")
    ordered = sorted(unique, key=lambda r: (r.family, r.number, r.code))
    return ordered, [*found, *by_code, *by_name]


def _unshared(
    rules: list[Rule], key: Callable[[Rule], str], noun: str
) -> tuple[list[Rule], list[Diagnostic]]:
    """Set aside the rules that share a code or a name.

    Args:
        rules: The rules.
        key: What they must not share.
        noun: How a message calls it, such as `the code`.

    Returns:
        The rules whose key is unique, and one error for each shared key that
        names every file with it, joined by `, `, in order.
    """
    groups: dict[str, list[Rule]] = {}
    for rule in rules:
        groups.setdefault(key(rule), []).append(rule)
    kept = [group[0] for group in groups.values() if len(group) == 1]
    errors = [
        _error(
            ", ".join(sorted(r.path.as_posix() for r in group)),
            f"Two rules share {noun} `{value}`",
        )
        for value, group in groups.items()
        if len(group) > 1
    ]
    return kept, errors
