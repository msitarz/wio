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

    Faults are errors, and everything else is still read; nothing is raised for
    a fault of the files. Each names its place, written with `/` and relative to
    `root`:

    - the file, followed by `:<line>` when the fault has a line, for a rule file
      that cannot be read, decoded or parsed, a rule of a family that its
      manifest does not declare, a `ruleset.toml` that is a symbolic link, one
      below a ruleset's directory, and a marked rule file directly in
      `.agents/wio/rules`;
    - the manifest followed by `#` and the key path for a key of a manifest;
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
