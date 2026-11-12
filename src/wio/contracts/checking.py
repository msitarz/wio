# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts check` reports about the Works."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from wio.contracts.actions import template_actions
from wio.contracts.discovery import discover_works, wrong_optional_fields
from wio.contracts.hierarchy import build_hierarchy
from wio.models.diagnostics import Diagnostic, has_error, order_diagnostics
lazy from wio.formats import closest_key, render_check

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Mapping
    from pathlib import Path

    from wio.contracts import Services
    from wio.contracts.actions import Pipeline
    from wio.contracts.hierarchy import Hierarchy
    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem, Stdio
    from wio.models.block import MetadataBlock
    from wio.models.config import Config
    from wio.models.template import Template
    from wio.models.works import Work

PASSES: Final = "The contracts pass."
"""What the command says when the check has nothing to report."""
_KNOWN_KEYS: Final = ("id", "template", "roots", "depends_on", "actions")
"""The keys of the metadata that wio reads, which an unknown key is compared to."""
_RESERVED_ID: Final = "none"
"""The id that stands for no Work in a record."""


def check_works(
    root: Path, config: Config, files: FileSystem, catalog: TemplateCatalog
) -> tuple[Diagnostic, ...]:
    """Find every problem of the Works, of their graph and of their metadata.

    It runs discovery and the hierarchy, and then one check for each concern of
    each Work, and reads and writes nothing else than through `files`. A problem
    found in one Work or by one check stops no other, and a Work with an error
    still gets the rest. Each Work's file is read again exactly once, and the
    block that it gives is shared by every concern, so that a later check of the
    body reads no third time and a file that cannot be read gives one error. Each
    template's `[actions]` are read at most once, however many Works follow it.
    What discovery and the hierarchy report is carried
    through and is not found again, and a check that depends on something already
    reported is skipped: the resolved actions of a Work whose template is missing,
    rejected or unreadable for its `[actions]`, or whose `template` or `[actions]`
    discovery reported as being of a wrong type, and the roots of a Work whose
    `roots` was reported. Which fields discovery reported is told by type-testing
    the block, which each Work's file is read for again; a file that cannot be
    read the second time is one error at the file, `The file cannot be read:
    <reason>`, or `The file is not valid UTF-8`, as discovery words them.
    Each diagnostic of this function names the Work's file as its place, without a
    line.

    The checks are these, each for every Work:

    - An unknown key of the metadata is a warning, ``Unknown key `k` in the
      metadata``, with ``. Did you mean `depends_on`?`` when `closest_key` finds
      one among `id`, `template`, `roots`, `depends_on` and `actions`. The table
      `[x]` and the key `tracks` are exempt and never suggested, a plain key `x`
      is unknown, and the `wio` marker is not a key.
    - An id that holds a character for which `str.isspace()` is true, or a comma,
      is an error, ``The id `a b` holds whitespace or a comma``, and so is the id
      `none`, ``The id `none` is reserved for commits that belong to no Work``.
    - A template that the catalog rejects is an error, ``The template `bad` is
      rejected by `wio templates check`; run it for the findings``, and one that
      it does not have is ``The template `nosuch` does not exist``.
    - A name in the Work's own `[actions]` is an error when it is not declared in
      the config: ``The action `a` is not declared in `[actions]` of the config``,
      ``The stage preset `p` of action `a` is not declared``, ``The stage `s` of
      action `a` is not declared``, and a stage twice in a list of stages that the
      Work or its template gives is ``The stage `s` appears twice in action `a```.
      A stage preset or a config default is not judged for repeats.
    - The actions that the Work resolves to, its template's under a named
      template and the config defaults under none, with its own over them, are an
      error, ``The Work resolves to no action``, when none is left.
    - A root that the Work names and the config does not declare is an error,
      ``The root `r` is not declared in `[roots]` of the config``, and
      `@descendants` is not a root. `@descendants` in a leaf is a warning, ``The
      Work has no children, so `@descendants` adds no root``. A parent whose
      resolved roots leave out a root that its descendants' resolved roots hold
      gets one note for each, ``Its roots leave out `r`, which a descendant
      uses``, declared or not, and none when its own `roots` was reported.

    Args:
        root: The repository root.
        config: The settings, which declare the actions, stage presets, stages and
            roots, the hierarchy mode, the Works directory and the defaults.
        files: The port that reads the Works' files and the templates' files.
        catalog: The port that finds a template and says whether it is rejected.

    Returns:
        Every diagnostic, the errors of discovery and of the graph and the
        findings of the checks together, in the order of `order_diagnostics`.

    Raises:
        ConfigurationError: The catalog could not load the config.
    """
    discovery = discover_works(root, config.works, files)
    found = build_hierarchy(discovery.works, config.works.hierarchy)
    run = _Run(root, config, files, catalog, found, _Templates(root, files))
    problems = [*discovery.diagnostics, *found.diagnostics]
    for work in found.works:
        problems.extend(_check_work(work, run))
    return order_diagnostics(problems)


class _Templates:
    """The `[actions]` of the templates, each read at most once."""

    def __init__(self, root: Path, files: FileSystem) -> None:
        """Keep what a read needs and start with none made.

        Args:
            root: The repository root.
            files: The port that reads the templates' files.
        """
        self._root = root
        self._files = files
        self._read: dict[str, Mapping[str, Pipeline] | None] = {}

    def actions(self, template: Template) -> Mapping[str, Pipeline] | None:
        """Give the actions of a template, reading its file the first time.

        Args:
            template: The template.

        Returns:
            What `template_actions` gave for it, the same for every Work.
        """
        if template.name not in self._read:
            self._read[template.name] = template_actions(
                template, self._root, self._files
            )
        return self._read[template.name]


@dataclass(frozen=True)
class _Run:
    """What every check of one run reads from.

    Attributes:
        root: The repository root.
        config: The settings.
        files: The port that reads the Works' files and the templates' files.
        catalog: The port that judges a template.
        found: The hierarchy of all the Works.
        templates: The actions of the templates, each read at most once.
    """

    root: Path
    config: Config
    files: FileSystem
    catalog: TemplateCatalog
    found: Hierarchy
    templates: _Templates


def _check_work(work: Work, run: _Run) -> list[Diagnostic]:
    """Run every check on one Work, none stopping another.

    Args:
        work: The Work.
        run: What the checks read from.

    Returns:
        The findings about the Work, in any order. A file that cannot be read the
        second time is the one error it gives.
    """
    block = _reread(run.root, work, run.files)
    if isinstance(block, Diagnostic):
        return [block]
    wrong = wrong_optional_fields(block.data)
    template, template_problems = _template_errors(work, run.catalog)
    return [
        *_key_warnings(work, block),
        *_id_error(work),
        *template_problems,
        *_named_errors(work, run.config),
        *_resolved_errors(work, template, wrong, run),
        *_root_errors(work, wrong, run.config, run.found),
    ]


def _reread(root: Path, work: Work, files: FileSystem) -> MetadataBlock | Diagnostic:
    """Read a Work's block again, once.

    Args:
        root: The repository root.
        work: The Work.
        files: The port that reads the file.

    Returns:
        The block, or the error at the file for one that cannot be read, decoded
        or parsed the second time.
    """
    raise NotImplementedError


def _key_warnings(work: Work, block: MetadataBlock) -> list[Diagnostic]:
    """Warn of each key of the metadata that wio does not know.

    Args:
        work: The Work, for the place.
        block: Its block.

    Returns:
        A warning for each unknown key with the closest known key when there is
        one, none for the table `x` and the key `tracks`.
    """
    place = work.path.as_posix()
    return [
        Diagnostic("warning", place, _unknown_key(key))
        for key, value in block.data.items()
        if key not in _KNOWN_KEYS and not _exempt(key, value)
    ]


def _exempt(key: str, value: object) -> bool:
    """Tell whether a key that wio does not read is left alone.

    Args:
        key: The key of the block.
        value: What it holds.

    Returns:
        Whether it is `tracks`, or `x` as a table.
    """
    return key == "tracks" or (key == "x" and isinstance(value, dict))


def _unknown_key(key: str) -> str:
    """Word the warning for an unknown key.

    Args:
        key: The key.

    Returns:
        The message, with the closest known key when there is one.
    """
    message = f"Unknown key `{key}` in the metadata"
    close = closest_key(key, _KNOWN_KEYS)
    return f"{message}. Did you mean `{close}`?" if close else message


def _id_error(work: Work) -> list[Diagnostic]:
    """Refuse an id that would break a record.

    Args:
        work: The Work.

    Returns:
        One error for an id that holds whitespace or a comma, one for `none`, and
        an empty list for another id.
    """
    place = work.path.as_posix()
    if any(char.isspace() or char == "," for char in work.id):
        message = f"The id `{work.id}` holds whitespace or a comma"
    elif work.id == _RESERVED_ID:
        message = f"The id `{work.id}` is reserved for commits that belong to no Work"
    else:
        return []
    return [Diagnostic("error", place, message)]


def _template_errors(
    work: Work, catalog: TemplateCatalog
) -> tuple[Template | None, list[Diagnostic]]:
    """Judge the template that a Work names.

    Args:
        work: The Work.
        catalog: The port that finds a template and says whether it is rejected.

    Returns:
        The template when the Work names one that exists and is not rejected, and
        `None` otherwise, with the error for a template that is missing or
        rejected and none for a Work that names no template.
    """
    raise NotImplementedError


def _named_errors(work: Work, config: Config) -> list[Diagnostic]:
    """Check the names in a Work's own `[actions]` against the config.

    Args:
        work: The Work.
        config: The settings, which declare the actions, stage presets and stages.

    Returns:
        An error for each action, stage preset and stage that is not declared and
        for a stage that a list gives twice. It runs for every Work, whatever its
        template.
    """
    raise NotImplementedError


def _resolved_errors(
    work: Work, template: Template | None, wrong: frozenset[str], run: _Run
) -> list[Diagnostic]:
    """Check what a Work resolves to.

    Args:
        work: The Work.
        template: The template that `_template_errors` gave.
        wrong: The fields that discovery reported.
        run: What the checks read from, for the defaults and the template's
            actions.

    Returns:
        The repeats of a stage that the Work inherits from its template, and the
        error that the Work resolves to no action. Nothing for a Work that names a
        template that is not usable, whose template or `[actions]` was reported, or
        whose template's file cannot be read for its `[actions]`.
    """
    raise NotImplementedError


def _root_errors(
    work: Work, wrong: frozenset[str], config: Config, found: Hierarchy
) -> list[Diagnostic]:
    """Check the roots a Work names and the roots its descendants use.

    Args:
        work: The Work.
        wrong: The fields that discovery reported.
        config: The settings, which declare the roots.
        found: The hierarchy, which resolves the roots.

    Returns:
        An error for each root that is not declared, a warning for `@descendants`
        in a leaf, and one note for each root of the descendants that the Work's
        resolved roots leave out, none when its `roots` was reported.
    """
    raise NotImplementedError


def run_check(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio contracts check`.

    It loads the config, finds every problem of the Works with `check_works`, and
    writes them with `render_check`, as the lines `<severity>: <where>: <message>`
    or, with `--json`, as one array, in the order `check_works` gives. It writes
    `The contracts pass.` when there is nothing to report. A warning or a note
    never fails the command.

    Args:
        services: What the command reads the project through.
        args: What the parser read: `json`, whether to write the array.
        stdio: Where the output goes.

    Returns:
        1 when a diagnostic is an error, otherwise 0.

    Raises:
        ConfigurationError: The config has an error, which the command line
            reports and exits 2 for.
    """
    config = services.settings.load()
    root = services.repository.root()
    found = check_works(root, config, services.files, services.catalog)
    stdio.stdout.write(render_check(found, as_json=args.json, passes=PASSES))
    return 1 if has_error(found) else 0
