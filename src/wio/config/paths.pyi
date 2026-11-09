# SPDX-License-Identifier: Apache-2.0
"""The checks of the paths, skills and templates that the config names.

Every function is a `Check` of `wio.config.checks`, and like those of
`wio.config.pipelines` it judges the best-effort `Config` as it stands and never
raises for a problem of the config. A path is judged as text and, for a missing
path or skill, against `CheckInputs.files` below `CheckInputs.root`; no check
reads a file's content, lists a directory or looks outside the repository. Every
`where` is a key path built with `join_path` and `item_path`. The checks are
appended to `wio.config.CHECKS`.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from wio.config.checks import CheckInputs
from wio.models.config import Config
from wio.models.diagnostics import Diagnostic

type Rule = Literal[
    "is empty", "is absolute", "leaves the repository", "is not normalized"
]
"""What is wrong with a path, as the phrase that follows it in a message."""

@dataclass(frozen=True)
class PathFault:
    """Why a path is not a normalized path inside the repository.

    A normalized path is relative to the repository root, with `/` as the
    separator and without a `.` or `..` segment, an empty segment, a trailing
    slash or a leading `/`; `.` alone is the whole repository. A message words a
    fault as "`<path>` <rule>", followed by "; use `<normalized>`" when there is
    a normalized form.

    Attributes:
        rule: What is wrong, one phrase for each kind of fault.
        normalized: The normalized form that names the same place inside the
            repository. Only `is not normalized` has one; an empty path, an
            absolute path and a path that leaves the repository have none.
    """

    rule: Rule
    normalized: str | None

def judge_path(path: str) -> PathFault | None:
    """Judge a path from the config as text, without reading the disk.

    Args:
        path: The path as the config writes it.

    Returns:
        `None` for a normalized path inside the repository. Otherwise the first
        fault that applies, in this order: `is empty`, `is absolute`, `leaves
        the repository` once the `.` and `..` segments are resolved, and `is not
        normalized`, whose `normalized` is the resolved form (`src/` is `src`,
        `a/./b` is `a/b`, `a/../b` is `b`, `src//x` is `src/x` and `./` is `.`).
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
        path whose normalized form, or itself when it has no fault, repeats an
        earlier one of the same root is an error that names the index of the
        first, instead of its fault; the same path in two roots is allowed. Any
        other path with a `PathFault` is an error that names the rule and the
        normalized form. A valid path that does not exist below the repository
        root and is the first of its kind is a warning, not an error, that says
        it does not exist yet. An empty path is a fault of this check, which the
        contract leaves to it.
    """
    ...

def check_skills(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that every skill a stage names is found, and where skills are sought.

    Args:
        config: The settings, whose stages and `skills.paths` are read.
        inputs: The repository root and the port whose `exists` tells whether
            `<root>/<dir>/<skill>/SKILL.md` exists; no other method is called.

    Returns:
        An error at `skills.paths[<i>]` for a path with a `PathFault`, saying
        that a skill path is normalized and stays inside the repository; paths
        are not checked for repeats here. An error at `stages.<name>.skill` for
        a skill that has no `SKILL.md` below `skills.paths`, `.agents/skills`
        or `.claude/skills`, searched in that order, with the paths that have a
        fault left out. It lists those directories, each once, as normalized
        paths relative to the repository in the order searched, and says the
        user's home is not searched. A skill name that is empty, or is `.` or
        `..` or has a `/`, is not found without a lookup. A stage with a `goal`
        is not judged.
    """
    ...

def check_templates(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the shape of the `[templates]` table.

    Args:
        config: The settings, whose `templates` table is read.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `templates.dir` for a path with a `PathFault`, and an error
        at `templates.kinds.<kind>` for a template name that is an empty string,
        each naming the key path and what a valid value is. The defaults are
        valid, so a config without the table gets no diagnostic.
    """
    ...

def check_works_dir(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that the Works directory is inside the repository.

    Args:
        config: The settings, whose `works.dir` is read.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `works.dir` for a path with a `PathFault`, saying that the
        path must be a normalized path inside the repository.
    """
    ...
