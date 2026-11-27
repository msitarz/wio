# SPDX-License-Identifier: Apache-2.0
"""What `wio rules list` shows: the view of the rules and its text and JSON."""

import os
from dataclasses import KW_ONLY, dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from wio.errors import WioError
lazy from wio.formats import Block, encode_json, render_blocks
lazy from wio.models.listing import Header, Listing, Row
lazy from wio.rules.anywhere import selected_anywhere
lazy from wio.rules.applicability import select
lazy from wio.rules.discovery import discover, refuse_on_errors
lazy from wio.rules.explaining import explain
lazy from wio.rules.inputs import ruleset_map
lazy from wio.rules.narrowing import narrow
lazy from wio.rules.roots import roots_of_path, stage_roots

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Mapping

    from wio.io.ports import Stdio
    from wio.models.config import Config
    from wio.models.rule import LoadedRuleset, Rule
    from wio.models.rules import Decision
    from wio.rules import Services
    from wio.rules.ports import WorkRoots


@dataclass(frozen=True)
class ListRequest:
    """What the arguments of `wio rules list` ask for.

    At most one of `root`, `path` and `work` is set. The leaves that narrow and
    explain the listing read `references`, `not_selected` and `explain`.

    Attributes:
        root: The name of a root whose rules to list.
        path: A file, relative to the repository root and written with `/`, whose
            roots to apply.
        work: The id of a Work whose roots to apply.
        stage: The name of a stage whose layer to apply.
        references: The references that narrow the listing.
        not_selected: Whether to list the rules that nothing selects.
        explain: Whether to explain where each rule came from.
        as_json: Whether to write one JSON object instead of the text.
    """

    root: str | None
    path: PurePosixPath | None
    work: str | None
    stage: str | None
    references: tuple[str, ...]
    _: KW_ONLY
    not_selected: bool
    explain: bool
    as_json: bool


def list_view(
    request: ListRequest,
    config: Config,
    rulesets: Mapping[str, LoadedRuleset],
    work_roots: WorkRoots,
) -> Listing:
    """Decide the rules of a view and describe what was applied.

    With no root, path, work or stage, no layer is applied and every rule is a
    row with no decision, in the order of C-2 of `wio rules`. With a root, a path
    or a Work, the roots apply, and with a stage its layer applies, together with
    the always fields; a stage alone leaves the roots not applied. A Work with a
    stage takes the roots that the stage selects. It does no input or output of
    its own.

    Args:
        request: The view asked for.
        config: The settings.
        rulesets: The rulesets by name, as `ruleset_map` gives them.
        work_roots: Gives the roots of a Work.

    Returns:
        The header and one row for every rule considered, with the decision where
        a layer was applied.

    Raises:
        KeyError: The stage, root or Work is not known.
        ValueError: The Work has no roots that the stage selects.
    """
    roots = _roots(request, config, work_roots)
    header = Header(
        _view(request),
        request.work,
        _layers(roots, request.stage),
        roots,
        request.stage,
        request.references,
        not_selected=request.not_selected,
    )
    if not header.layers:
        return Listing(header, _undecided(rulesets))
    chosen = select(roots, request.stage, config, rulesets)
    return Listing(header, tuple(Row(r, d, (), None) for r, d in chosen.items()))


def _roots(
    request: ListRequest, config: Config, work_roots: WorkRoots
) -> tuple[str, ...] | None:
    """Find the roots that a request applies."""
    if request.root is not None:
        return (request.root,)
    if request.path is not None:
        return roots_of_path(config, request.path)
    if request.work is not None:
        return stage_roots(config, request.stage, request.work, work_roots)
    return None


def _view(request: ListRequest) -> str:
    """Name the view of a request."""
    if request.root is not None:
        return f"root {request.root}"
    if request.path is not None:
        return f"file {request.path.as_posix()}"
    if request.work is not None:
        return f"Work {request.work}"
    if request.stage is not None:
        return f"stage {request.stage}"
    return "every rule"


def _layers(roots: tuple[str, ...] | None, stage: str | None) -> tuple[str, ...]:
    """Name the layers a view applies."""
    names = [("roots", roots is not None), ("stage", stage is not None)]
    found = [name for name, applied in names if applied]
    return (*found, "always fields") if found else ()


def _undecided(rulesets: Mapping[str, LoadedRuleset]) -> tuple[Row, ...]:
    """Make a row with no decision for every rule."""
    return tuple(
        Row(rule, None, (), None)
        for name in sorted(rulesets)
        for rule in sorted(rulesets[name].rules, key=_order)
    )


def _order(rule: Rule) -> tuple[str, int, str]:
    """Order the rules of a ruleset."""
    return rule.family, rule.number, rule.code


def _shown(row: Row, *, marked: bool) -> bool:
    """Decide whether the renderer shows a row."""
    included = row.decision is None or row.decision.included
    return included or row.explanation is not None or marked


def render_listing(listing: Listing, *, as_json: bool) -> str:
    """Render a listing for a person or for a program.

    A row is shown when its rule is included or has no decision, when it has an
    explanation, or when the header is marked `not selected`. The text is the
    header lines, a blank line and one block for each shown row through
    `render_blocks`, with a blank line between one block and the next; the JSON
    is one object on one line through `encode_json`, with the header keys and
    then the rules, whose fields are followed by those of the explanation. It
    reads and writes nothing.

    Args:
        listing: The listing.
        as_json: Whether to render the object instead of the text.

    Returns:
        The text for standard output, ending in a newline.
    """
    marked = listing.header.not_selected
    shown = [row for row in listing.rows if _shown(row, marked=marked)]
    if as_json:
        return encode_json(_as_object(listing.header, shown)) + "\n"
    lines = "".join(f"{line}\n" for line in _header_lines(listing.header))
    return lines + "\n" + render_blocks([_block(row) for row in shown], spaced=True)


def _header_lines(header: Header) -> list[str]:
    """Write the header lines of the text."""
    roots = "not applied" if header.roots is None else ", ".join(header.roots)
    lines = [
        f"view: {header.view}",
        f"layers: {', '.join(header.layers) or 'none'}",
        f"roots: {roots or 'none'}",
    ]
    if header.stage is not None and header.view != f"stage {header.stage}":
        lines.append(f"stage: {header.stage}")
    if header.references:
        lines.append("references: " + ", ".join(header.references))
    if header.not_selected:
        lines.append("filter: not selected")
    return lines


def _block(row: Row) -> Block:
    """Lay out one row as a block."""
    rule, decision = row.rule, row.decision
    details = [rule.description or rule.summary, _roots_line(decision)]
    if row.explanation is not None:
        details.extend(row.explanation.lines())
    return Block(0, rule.qualified, rule.name, None, tuple(d for d in details if d))


def _roots_line(decision: Decision | None) -> str:
    """Write the `roots:` line of a rule."""
    if decision is None or not decision.included:
        return ""
    roots = "every root" if decision.root_independent else ", ".join(decision.roots)
    return f"roots: {roots or 'none'}"


def _as_object(header: Header, rows: list[Row]) -> dict[str, object]:
    """Describe a listing as plain data for JSON."""
    return {
        "view": header.view,
        "work": header.work,
        "layers": list(header.layers),
        "roots": None if header.roots is None else list(header.roots),
        "stage": header.stage,
        "references": list(header.references),
        "not_selected": header.not_selected,
        "rules": [_rule_object(row) for row in rows],
    }


def _rule_object(row: Row) -> dict[str, object]:
    """Describe a row as plain data for JSON."""
    rule, decision = row.rule, row.decision
    found: dict[str, object] = {
        "code": rule.qualified,
        "name": rule.name,
        "description": rule.description,
        "summary": rule.summary,
        "roots": None if decision is None else list(decision.roots),
        "root_independent": None if decision is None else decision.root_independent,
        "included": True if decision is None else decision.included,
    }
    if row.explanation is not None:
        found.update(row.explanation.fields())
    return found


def run_list(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules list`.

    It runs the discovery once, refuses a fault in the rules, a selector that
    cannot be used and a reference that cannot be used before anything is
    printed, builds the listing of the view, narrows and explains it as asked and
    writes it.

    Args:
        services: What the command reads the project through.
        args: The parsed arguments.
        stdio: Where the listing goes.

    Returns:
        0 after the listing.

    Raises:
        WioError: A selector or a reference cannot be used: an unknown stage,
            root or Work, a Work with no roots, a path outside the repository, or
            a reference that names nothing. It names the cause, so the command
            exits 2.
        DiagnosticsError: The discovery reported an error.
        ConfigurationError: The config has an error.
    """
    config = services.settings.load()
    root = services.repository.root()
    request = _request(args, root, services.environment.working_directory())
    discovery = discover(root, services.files)
    refuse_on_errors(discovery)
    rulesets = ruleset_map(discovery)
    try:
        listing = list_view(request, config, rulesets, services.work_roots)
    except KeyError as error:
        raise WioError(_unknown(error.args[0], request)) from error
    except ValueError as error:
        raise WioError(str(error)) from error
    listing = _refined(listing, request, config, rulesets)
    stdio.stdout.write(render_listing(listing, as_json=request.as_json))
    return 0


def _refined(
    listing: Listing,
    request: ListRequest,
    config: Config,
    rulesets: Mapping[str, LoadedRuleset],
) -> Listing:
    """Narrow and explain a listing as the request asks."""
    if not (request.references or request.not_selected or request.explain):
        return listing
    anywhere = selected_anywhere(config, rulesets)
    if request.references or request.not_selected:
        listing = narrow(
            listing,
            request.references,
            not_selected=request.not_selected,
            config=config,
            rulesets=rulesets,
            anywhere=anywhere,
        )
    return explain(listing, anywhere) if request.explain else listing


def _request(args: Namespace, root: Path, cwd: Path) -> ListRequest:
    """Read the request from the arguments."""
    path = None if args.path is None else _inside(root, cwd, args.path)
    return ListRequest(
        args.root,
        path,
        args.work,
        args.stage,
        tuple(args.references),
        not_selected=args.not_selected,
        explain=args.explain,
        as_json=args.json,
    )


def _inside(root: Path, cwd: Path, text: str) -> PurePosixPath:
    """Make a path relative to the repository root."""
    absolute = Path(os.path.normpath(cwd / text))
    if not absolute.is_relative_to(root):
        message = f"The path `{text}` is outside the repository."
        raise WioError(message)
    return PurePosixPath(absolute.relative_to(root).as_posix())


def _unknown(name: object, request: ListRequest) -> str:
    """Say which name of the request is not known."""
    if name == request.stage:
        return f"The config has no stage `{name}`."
    if name == request.work:
        return f"No Work `{name}` is known."
    return f"The config has no root `{name}`."
