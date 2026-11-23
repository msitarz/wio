# SPDX-License-Identifier: Apache-2.0
"""Finding the rulesets of a repository and reading their manifests and rules."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.diagnostics import Diagnostic
    from wio.models.rule import LoadedRuleset


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

    Faults are errors that name their place, and everything else is still read:
    a rules directory that is a symbolic link or not a directory, which is not
    walked; a directory that cannot be listed; a ruleset directory that is a
    symbolic link or whose name has the wrong form; a missing or unreadable
    `ruleset.toml`, one that is a symbolic link, and one below a ruleset's
    directory; a file that is not valid UTF-8 or cannot be read; and a marked
    rule file directly in `.agents/wio/rules`. A missing rules directory is no
    fault. Nothing is raised for a fault of the files.

    Args:
        root: The repository root.
        files: The port that lists directories and reads files.

    Returns:
        The rulesets and the diagnostics.
    """
    del root, files
    msg = "discover is declared by the architecture stage"
    raise NotImplementedError(msg)


def refuse_on_errors(discovery: Discovery) -> None:
    """Refuse a discovery that has an error.

    Args:
        discovery: What `discover` returned.

    Raises:
        DiagnosticsError: The discovery holds an error. It carries the error
            diagnostics, in order, and not the warnings.
    """
    del discovery
    msg = "refuse_on_errors is declared by the architecture stage"
    raise NotImplementedError(msg)
