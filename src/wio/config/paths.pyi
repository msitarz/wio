# SPDX-License-Identifier: Apache-2.0
"""The checks of the paths, skills and templates that the config names.

Every function is a `Check` of `wio.config.checks`, and like those of
`wio.config.pipelines` it judges the best-effort `Config` as it stands and never
raises for a problem of the config. A path is judged as text and, for a missing
path or skill, against `CheckInputs.files` below `CheckInputs.root` through its
`exists` alone; no check reads a file's content, lists a directory or looks
outside the repository. Every `where` is a key path built with `join_path` and
`item_path`, and a message words its names and lists with `quoted` and
`and_list` of `wio.config.messages`. The checks are appended to
`wio.config.CHECKS`.

A fault of a path is worded "`<path>` <rule>" and, when there is a normalized
form, "; use `<normalized>`", followed by a sentence of the check that judges
it; each check below gives its sentence.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from wio.config.checks import CheckInputs
from wio.models.config import Config
from wio.models.diagnostics import Diagnostic

@dataclass(frozen=True)
class Unusable:
    """A path that has no normalized form inside the repository.

    Attributes:
        rule: The phrase that follows the path in a message: `is empty`, `is
            absolute`, or `leaves the repository` once its `.` and `..` segments
            are resolved.
    """

    rule: Literal["is empty", "is absolute", "leaves the repository"]

@dataclass(frozen=True)
class NotNormalized:
    """A path inside the repository that is not written in its normalized form.

    Attributes:
        normalized: The normalized form that names the same place, with `/` as
            the separator and without a `.` or `..` segment, an empty segment,
            a trailing slash or a leading `/`; `.` alone is the whole
            repository. Its rule is `is not normalized`.
    """

    normalized: str

type PathFault = Unusable | NotNormalized
"""Why a path is not a normalized path inside the repository."""

def judge_path(path: str) -> PathFault | None:
    """Judge a path from the config as text, without reading the disk.

    Args:
        path: The path as the config writes it.

    Returns:
        `None` for a normalized path inside the repository. Otherwise the first
        fault that applies, in this order: `is empty`, `is absolute`, `leaves
        the repository`, and not normalized, whose form is the resolved path
        (`src/` is `src`, `a/./b` is `a/b`, `a/../b` is `b`, `src//x` is
        `src/x` and `./` is `.`).
    """
    ...

def check_root_paths(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the paths of every root.

    Args:
        config: The settings, whose roots are read.
        inputs: The repository root and the port whose `exists` tells whether a
            path exists below it.

    Returns:
        At most one diagnostic for each path, at `roots.<name>.paths[<i>]`. A
        path whose resolved form repeats that of an earlier path of the same
        root, a path without a fault resolving to itself, is an error that says
        it repeats the path at the full key path of the first, such as
        `roots.b.paths[0]`, instead of its fault, when it has a normalized form;
        the same path in two roots is allowed. Any other path with a fault is an
        error worded as the module says, with no further sentence. A path that
        has no fault, is not a repeat of an earlier path of its root and does not
        exist below the repository root is a warning that says it does not exist
        yet. An empty path is a fault of this check, which the contract leaves to
        it.
    """
    ...

def check_skills(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that every skill a stage names is found, and where skills are sought.

    Args:
        config: The settings, whose stages and `skills.paths` are read.
        inputs: The repository root and the port whose `exists` tells whether
            `<root>/<dir>/<skill>/SKILL.md` exists; no other method is called.

    Returns:
        An error at `skills.paths[<i>]` for a path with a fault, worded as the
        module says and followed by "The path must stay inside the repository.";
        paths are not checked for repeats here. An error at
        `stages.<name>.skill` for a skill that has no `SKILL.md` below
        `skills.paths`, `.agents/skills` or `.claude/skills`, searched in that
        order, with the paths that have a fault, a normalized form among them,
        left out. Its message lists those directories, each once, as normalized
        paths relative to the repository in the order searched, and says "the
        user's home is not searched". A skill name that is empty, or is `.` or
        `..` or has a `/`, is not found without a lookup. A stage with a `goal`
        is not judged, and a stage that has both is left to the shape.
    """
    ...

def check_templates(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the shape of the `[templates]` table.

    Args:
        config: The settings, whose `templates` table is read.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `templates.dir` for a path with a fault, worded as the module
        says and followed by "A templates directory is a normalized path inside
        the repository.". An error at `templates.kinds.<kind>` for a template
        name that is an empty string, saying that the template name is empty and
        that a kind names a template with a non-empty string; the message does
        not repeat the key path. The defaults are valid, so a config without the
        table gets no diagnostic.
    """
    ...

def check_works_dir(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that the Works directory is inside the repository.

    Args:
        config: The settings, whose `works.dir` is read.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `works.dir` for a path with a fault, worded as the module
        says and followed by "The path must be inside the repository.".
    """
    ...
