# SPDX-License-Identifier: Apache-2.0
"""Finding the rulesets of a repository and reading their manifests and rules."""

from dataclasses import dataclass
from functools import partial
from pathlib import Path, PurePosixPath
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
    """Walk `.agents/wio/rules` and read each ruleset."""
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
    """List the entries of `.agents/wio/rules`, unless it must not be walked."""
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
    raise DiagnosticsError(render_text(errors), errors)


def _place(root: Path, path: Path) -> str:
    """Write the place of a path."""
    return path.relative_to(root).as_posix()


def _unlistable(place: str, error: OSError) -> Diagnostic:
    """Make the error of a directory that cannot be listed."""
    return _error(place, f"The directory cannot be listed: {error.strerror}")


def _read_entry(
    root: Path, entry: Path, files: FileSystem
) -> tuple[list[LoadedRuleset], list[Diagnostic]]:
    """Judge one entry directly under the rules directory."""
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
    """Judge a file directly under the rules directory."""
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
    """Read the manifest and the rules of one ruleset directory."""
    place = _place(root, directory)
    try:
        paths = list(_walk(directory, files))
    except OSError as error:
        return None, _unlistable_ruleset(root, directory, error, files)
    manifest, found = _read_manifest(root, directory, files)
    found.extend(_nested_manifests(root, directory, paths))
    if manifest is None:
        return None, found
    markdown = sorted(p for p in paths if p.name.endswith(_SUFFIX))
    rules, problems = _read_rules(root, directory.name, markdown, files)
    kept, relations = _relate(rules, manifest)
    ruleset = LoadedRuleset(directory.name, PurePosixPath(place), manifest, tuple(kept))
    return ruleset, [*found, *problems, *relations]


def _unlistable_ruleset(
    root: Path, directory: Path, error: OSError, files: FileSystem
) -> list[Diagnostic]:
    """Report a ruleset directory, or one below it, that cannot be listed."""
    place = _place(root, directory)
    where = _failed_at(root, error, place)
    problem = _unlistable(where, error)
    if where == place:
        return [problem]
    return [*_read_manifest(root, directory, files)[1], problem]


def _failed_at(root: Path, error: OSError, default: str) -> str:
    """Find the place that an operating system error names."""
    named = Path(str(error.filename)) if error.filename else None
    if named is None or not named.is_relative_to(root):
        return default
    return _place(root, named)


def _nested_manifests(
    root: Path, directory: Path, paths: list[Path]
) -> list[Diagnostic]:
    """Find the manifests below a ruleset's directory, which are never read."""
    message = "A manifest is not read below a ruleset's directory"
    return [
        _error(_place(root, path), message)
        for path in paths
        if path.name == _MANIFEST and path.parent != directory
    ]


def _read_manifest(
    root: Path, directory: Path, files: FileSystem
) -> tuple[Manifest | None, list[Diagnostic]]:
    """Read the `ruleset.toml` of a ruleset directory."""
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
    """List the files below a ruleset's directory, whatever their names."""
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
    """Read the Markdown files of a ruleset that are rules."""
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
    """Judge the rules of one ruleset against its manifest and each other."""
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
    """Set aside the rules that share a code or a name."""
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
