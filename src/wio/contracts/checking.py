# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts check` reports about the Works."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal

from wio.contracts.actions import resolve_actions, template_actions
from wio.contracts.body import BodyChecker
from wio.contracts.discovery import discover_works, wrong_optional_fields
from wio.contracts.hierarchy import build_hierarchy
from wio.contracts.roots import DESCENDANTS, undeclared_root
from wio.formats.errors import MetadataBlockError
from wio.models.diagnostics import Diagnostic, has_error, order_diagnostics
lazy from wio.formats import closest_key, read_metadata_block, render_check

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Mapping
    from pathlib import Path

    from wio.contracts import Services
    from wio.contracts.actions import Pipeline, ResolvedAction
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
    """Validate all Works, their dependency graph, metadata, and bodies.

    Runs discovery, hierarchy building, metadata checks (keys, ids, templates,
    actions, roots), and body checks via `BodyChecker`. Collects all findings
    in one pass without short-circuiting, skipping only checks whose inputs
    already failed discovery.

    Returns:
        All diagnostics ordered by `order_diagnostics`.

    Raises:
        ConfigurationError: If the template catalog cannot load the config.
    """
    discovery = discover_works(root, config.works, files)
    found = build_hierarchy(discovery.works, config.works.hierarchy)
    run = _Run(
        root,
        config,
        files,
        catalog,
        found,
        _Templates(root, files),
        BodyChecker(root, files),
    )
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
    """What every check of one run reads from."""

    root: Path
    config: Config
    files: FileSystem
    catalog: TemplateCatalog
    found: Hierarchy
    templates: _Templates
    bodies: BodyChecker


def _check_work(work: Work, run: _Run) -> list[Diagnostic]:
    """Run every check on one Work, none stopping another."""
    block = _reread(run.root, work, run.files)
    if isinstance(block, Diagnostic):
        return [block]
    wrong = wrong_optional_fields(block.data)
    template, template_problems = _template_errors(work, run.catalog)
    body = [] if "template" in wrong else run.bodies.check(work, block, template)
    return [
        *_key_warnings(work, block),
        *_id_error(work),
        *template_problems,
        *_named_errors(work, run.config),
        *_resolved_errors(work, template, wrong, run),
        *_root_errors(work, wrong, run.config, run.found),
        *body,
    ]


def _reread(root: Path, work: Work, files: FileSystem) -> MetadataBlock | Diagnostic:
    """Read a Work's block again, once."""
    place = work.path.as_posix()
    try:
        block = read_metadata_block(files.read_text(root / work.path))
    except UnicodeDecodeError:
        return Diagnostic("error", place, "The file is not valid UTF-8")
    except OSError as error:
        reason = f"The file cannot be read: {error.strerror}"
        return Diagnostic("error", place, reason)
    except MetadataBlockError as error:
        return Diagnostic("error", f"{place}:{error.line}", error.message)
    if block is None:
        return Diagnostic("error", place, "The file has no metadata block any more")
    return block


def _key_warnings(work: Work, block: MetadataBlock) -> list[Diagnostic]:
    """Warn of each key of the metadata that wio does not know."""
    place = work.path.as_posix()
    return [
        Diagnostic("warning", place, _unknown_key(key))
        for key, value in block.data.items()
        if key not in _KNOWN_KEYS and not _exempt(key, value)
    ]


def _exempt(key: str, value: object) -> bool:
    """Tell whether a key that wio does not read is left alone."""
    return key == "tracks" or (key == "x" and isinstance(value, dict))


def _unknown_key(key: str) -> str:
    """Word the warning for an unknown key."""
    message = f"Unknown key `{key}` in the metadata"
    close = closest_key(key, _KNOWN_KEYS)
    return f"{message}. Did you mean `{close}`?" if close else message


def _id_error(work: Work) -> list[Diagnostic]:
    """Refuse an id that would break a record."""
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
    """Judge the template that a Work names."""
    name = work.template
    if name is None:
        return None, []
    if catalog.is_rejected(name):
        message = (
            f"The template `{name}` is rejected by `wio templates check`; "
            "run it for the findings"
        )
        return None, [Diagnostic("error", work.path.as_posix(), message)]
    template = catalog.find(name)
    if template is None:
        message = f"The template `{name}` does not exist"
        return None, [Diagnostic("error", work.path.as_posix(), message)]
    return template, []


def _named_errors(work: Work, config: Config) -> list[Diagnostic]:
    """Check the names in a Work's own `[actions]` against the config."""
    place = work.path.as_posix()
    messages: list[str] = []
    for name, pipeline in work.actions.items():
        if name not in config.actions:
            messages.append(
                f"The action `{name}` is not declared in `[actions]` of the config"
            )
        messages.extend(_pipeline_problems(name, pipeline, config))
    return [Diagnostic("error", place, message) for message in messages]


def _pipeline_problems(action: str, pipeline: Pipeline, config: Config) -> list[str]:
    """Judge one pipeline that a Work or a template gives."""
    if isinstance(pipeline, str):
        if pipeline in config.stage_presets:
            return []
        return [f"The stage preset `{pipeline}` of action `{action}` is not declared"]
    stages = list(dict.fromkeys(pipeline))
    problems = [
        f"The stage `{stage}` of action `{action}` is not declared"
        for stage in stages
        if stage not in config.stages
    ]
    problems.extend(
        f"The stage `{stage}` appears twice in action `{action}`"
        for stage in _repeated(pipeline)
    )
    return problems


def _repeated(stages: tuple[str, ...]) -> list[str]:
    """Name each stage that a list of stages gives twice."""
    seen: set[str] = set()
    return list(dict.fromkeys(s for s in stages if s in seen or seen.add(s)))


def _resolved_errors(
    work: Work, template: Template | None, wrong: frozenset[str], run: _Run
) -> list[Diagnostic]:
    """Check what a Work resolves to."""
    if {"template", "actions"} & wrong or (work.template and template is None):
        return []
    inherited, source = _inherited(template, run)
    if inherited is None:
        return []
    resolved = resolve_actions(work.actions, inherited, source)
    problems = _inherited_repeats(resolved)
    if all(entry.removed for entry in resolved):
        problems.append("The Work resolves to no action")
    place = work.path.as_posix()
    return [Diagnostic("error", place, message) for message in problems]


def _inherited_repeats(resolved: tuple[ResolvedAction, ...]) -> list[str]:
    """Name the repeats of a stage that a Work inherits from its template."""
    return [
        f"The stage `{stage}` appears twice in action `{entry.name}`"
        for entry in resolved
        if entry.source == "template" and isinstance(entry.pipeline, tuple)
        for stage in _repeated(entry.pipeline)
    ]


def _inherited(
    template: Template | None, run: _Run
) -> tuple[Mapping[str, Pipeline] | None, Literal["template", "defaults"]]:
    """Find the actions that a Work inherits."""
    if template is None:
        return run.config.works.defaults.actions, "defaults"
    return run.templates.actions(template), "template"


def _root_errors(
    work: Work, wrong: frozenset[str], config: Config, found: Hierarchy
) -> list[Diagnostic]:
    """Check the roots a Work names and the roots its descendants use."""
    place = work.path.as_posix()
    undeclared = [
        Diagnostic(
            "error",
            place,
            f"The root `{root}` is not declared in `[roots]` of the config",
        )
        for root in dict.fromkeys(work.roots)
        if undeclared_root(root, config.roots)
    ]
    notes = [] if "roots" in wrong else _omission_notes(work, found)
    return [*undeclared, *_leaf_warning(work, found), *notes]


def _leaf_warning(work: Work, found: Hierarchy) -> list[Diagnostic]:
    """Warn of `@descendants` in a Work that has no children."""
    if DESCENDANTS not in work.roots or found.children[work.path]:
        return []
    message = "The Work has no children, so `@descendants` adds no root"
    return [Diagnostic("warning", work.path.as_posix(), message)]


def _omission_notes(work: Work, found: Hierarchy) -> list[Diagnostic]:
    """Note each root of the descendants that a Work's roots leave out."""
    place = work.path.as_posix()
    return [
        Diagnostic(
            "note", place, f"Its roots leave out `{root}`, which a descendant uses"
        )
        for root in _omitted_roots(work, found)
    ]


def _omitted_roots(work: Work, found: Hierarchy) -> list[str]:
    """Find the roots of the descendants that a Work's own roots leave out."""
    used = {
        root for kid in found.descendants[work.path] for root in found.roots[kid.path]
    }
    return sorted(used - set(found.roots[work.path]))


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
