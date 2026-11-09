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

from wio.config.checks import CheckInputs
from wio.models.config import Config
from wio.models.diagnostics import Diagnostic

@dataclass(frozen=True)
class PathFault:
    """Why a path is not a normalized path inside the repository.

    A normalized path is relative to the repository root, with `/` as the
    separator and without a `.` or `..` segment, an empty segment, a trailing
    slash or a leading `/`; `.` alone is the whole repository.

    Attributes:
        rule: What is wrong, as a phrase that follows the path in a message,
            such as `is absolute`, `leaves the repository` or `ends with a
            slash`.
        normalized: The normalized form that names the same place inside the
            repository, or `None` when there is none, as for an absolute path
            or one that leaves the repository.
    """

    rule: str
    normalized: str | None

def judge_path(path: str) -> PathFault | None:
    """Judge a path from the config as text, without reading the disk.

    Args:
        path: The path as the config writes it.

    Returns:
        `None` for a normalized path inside the repository. Otherwise the first
        fault that applies, in this order: an empty string, an absolute path, a
        path that leaves the repository once its `.` and `..` segments are
        resolved, and a path that is not normalized, whose `normalized` is the
        resolved form (`src/` is `src`, `a/./b` is `a/b`, `a/../b` is `b`, and
        `./` is `.`). An empty string and a path that leaves the repository
        have no normalized form.
    """
    ...

def check_root_paths(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the paths of every root.

    Args:
        config: The settings, whose roots are read.
        inputs: The repository root and the port that tells whether a path
            exists.

    Returns:
        An error at `roots.<name>.paths[<i>]` for a path with a `PathFault`,
        naming the rule and the normalized form where there is one. An error at
        the later path of two that are equal once normalized, within one root,
        naming the index of the first; a path that has a fault is judged by its
        normalized form when it has one, and the same path in two roots is
        allowed. A warning at the path, and no error, for a valid path that does
        not exist below the repository root yet, saying so.
    """
    ...

def check_skills(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that every skill a stage names is found, and where skills are sought.

    Args:
        config: The settings, whose stages and `skills.paths` are read.
        inputs: The repository root and the port that tells whether a file
            exists.

    Returns:
        An error at `skills.paths[<i>]` for a path with a `PathFault`, saying
        that a skill path is normalized and stays inside the repository. An
        error at `stages.<name>.skill` for a skill that has no
        `<dir>/<skill>/SKILL.md` in `skills.paths`, `.agents/skills` or
        `.claude/skills`, searched in that order, which lists those directories
        in that order, the paths that have a fault left out, and says that the
        user's home is not searched. A stage with a `goal` is not judged.
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
