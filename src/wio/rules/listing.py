# SPDX-License-Identifier: Apache-2.0
"""What `wio rules list` shows: the view of the rules and its text and JSON."""

from dataclasses import KW_ONLY, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Mapping
    from pathlib import PurePosixPath

    from wio.io.ports import Stdio
    from wio.models.config import Config
    from wio.models.listing import Listing
    from wio.models.rule import LoadedRuleset
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
    del request, config, rulesets, work_roots
    raise NotImplementedError


def render_listing(listing: Listing, *, as_json: bool) -> str:
    """Render a listing for a person or for a program.

    A row is shown when its rule is included or has no decision, when it has an
    explanation, or when the header is marked `not selected`. The text is the
    header lines, a blank line and one block for each shown row through
    `render_blocks`; the JSON is one object on one line through `encode_json`,
    with the header keys and then the rules, whose fields are followed by those
    of the explanation. It reads and writes nothing.

    Args:
        listing: The listing.
        as_json: Whether to render the object instead of the text.

    Returns:
        The text for standard output, ending in a newline.
    """
    del listing, as_json
    raise NotImplementedError


def run_list(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Run `wio rules list`.

    It runs the discovery once, refuses a fault in the rules and a selector that
    cannot be used before anything is printed, and writes the listing.

    Args:
        services: What the command reads the project through.
        args: The parsed arguments.
        stdio: Where the listing goes.

    Returns:
        0 after the listing.

    Raises:
        WioError: A selector cannot be used: an unknown stage, root or Work, a
            Work with no roots, or a path outside the repository. It names the
            cause, so the command exits 2.
        DiagnosticsError: The discovery reported an error.
        ConfigurationError: The config has an error.
    """
    del services, args, stdio
    raise NotImplementedError
