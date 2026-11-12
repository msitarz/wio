# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts check` reports about the Works."""

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from argparse import Namespace
    from pathlib import Path

    from wio.contracts import Services
    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem, Stdio
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic

PASSES: Final = "The contracts pass."
"""What the command says when the check has nothing to report."""


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
    raise NotImplementedError
