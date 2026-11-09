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

from dataclasses import dataclass
from functools import partial
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Literal

from wio.config.messages import and_list, item_path, join_path
from wio.models.diagnostics import Diagnostic

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from wio.config.checks import CheckInputs
    from wio.models.config import Config

_SKILL_DIRECTORIES = (".agents/skills", ".claude/skills")
_SKILL_FILE = "SKILL.md"

# Builds the error at a key path: `_error(where, message)`.
_error = partial(Diagnostic, "error")


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
        (`src/` is `src`, `a/./b` is `a/b`, `src//x` is `src/x`, `a/../b` is
        `b` and `./` is `.`).
    """
    if not path:
        return Unusable("is empty")
    if path.startswith("/"):
        return Unusable("is absolute")
    resolved = _resolve(path)
    if resolved is None:
        return Unusable("leaves the repository")
    return None if resolved == path else NotNormalized(resolved)


def check_root_paths(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the paths of every root.

    Args:
        config: The settings, whose roots are read.
        inputs: The repository root and the port whose `exists` tells whether a
            path exists below it.

    Returns:
        At most one diagnostic for each path, at `roots.<name>.paths[<i>]`: an
        error that says it repeats the path at the full key path of the first
        when its resolved form repeats that of an earlier path of the same root,
        instead of its fault; an error for any other fault; and, for a path with
        none that is not a repeat, a warning when it does not exist below the
        repository root. The same path in two roots is allowed.
    """
    for name, root in config.roots.items():
        where = join_path(join_path("roots", name), "paths")
        yield from _root_paths(where, root.paths, inputs)


def check_skills(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that every skill a stage names is found, and where skills are sought.

    Args:
        config: The settings, whose stages and `skills.paths` are read.
        inputs: The repository root and the port whose `exists` tells whether
            `<root>/<dir>/<skill>/SKILL.md` exists; no other method is called.

    Returns:
        An error at `skills.paths[<i>]` for a path with a fault, and an error at
        `stages.<name>.skill` for a skill that is found in none of the directories
        searched, `skills.paths`, `.agents/skills` and `.claude/skills` in that
        order, with the paths that have a fault left out. A stage with a `goal`
        is not judged, and a stage that has both is left to the shape.
    """
    yield from _skill_path_faults(config.skills.paths)
    valid = [path for path in config.skills.paths if judge_path(path) is None]
    searched = list(dict.fromkeys([*valid, *_SKILL_DIRECTORIES]))
    for name, stage in config.stages.items():
        skill = stage.skill
        if (
            stage.goal is None
            and skill is not None
            and not _found(skill, searched, inputs)
        ):
            yield _missing_skill(name, skill, searched)


def check_templates(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check the shape of the `[templates]` table.

    Args:
        config: The settings, whose `templates` table is read.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `templates.dir` for a path with a fault, and an error at
        `templates.kinds.<kind>` for a template name that is an empty string.
    """
    del inputs
    templates = config.templates
    fault = judge_path(templates.dir)
    if fault is not None:
        sentence = "A templates directory is a normalized path inside the repository."
        yield _fault("templates.dir", templates.dir, fault, sentence)
    for kind, template in templates.kinds.items():
        if template == "":
            yield _error(
                join_path("templates.kinds", kind),
                "the template name is empty; a kind names a template with a "
                "non-empty string.",
            )


def check_works_dir(config: Config, inputs: CheckInputs) -> Iterable[Diagnostic]:
    """Check that the Works directory is inside the repository.

    Args:
        config: The settings, whose `works.dir` is read.
        inputs: Unused; the check reads no file.

    Returns:
        An error at `works.dir` for a path with a fault.
    """
    del inputs
    fault = judge_path(config.works.dir)
    if fault is not None:
        sentence = "The path must be inside the repository."
        yield _fault("works.dir", config.works.dir, fault, sentence)


def _root_paths(
    where: str, paths: Sequence[str], inputs: CheckInputs
) -> Iterable[Diagnostic]:
    """Judge the paths of one root.

    Args:
        where: The key path of the list.
        paths: The paths as written.
        inputs: The repository root and the port that tells whether one exists.

    Returns:
        At most one diagnostic for each path, as `check_root_paths` says.
    """
    first: dict[str, int] = {}
    for index, path in enumerate(paths):
        fault = judge_path(path)
        form = _form(path, fault)
        at = item_path(where, index)
        if form in first:
            earlier = item_path(where, first[form])
            yield _error(at, f"`{path}` repeats the path at `{earlier}`.")
            continue
        if form is not None:
            first[form] = index
        found = _root_path(at, path, fault, inputs)
        if found is not None:
            yield found


def _skill_path_faults(paths: Sequence[str]) -> Iterable[Diagnostic]:
    """Judge the paths of `skills.paths`, which need not be unique.

    Args:
        paths: The paths as written.

    Returns:
        An error for each path with a fault.
    """
    sentence = "The path must stay inside the repository."
    for index, path in enumerate(paths):
        fault = judge_path(path)
        if fault is not None:
            yield _fault(item_path("skills.paths", index), path, fault, sentence)


def _resolve(path: str) -> str | None:
    """Resolve the `.` and `..` segments of a relative path.

    Args:
        path: A relative path.

    Returns:
        The normalized form, `.` for the whole repository, or `None` when the
        path leaves the repository.
    """
    kept: list[str] = []
    for part in PurePosixPath(path).parts:
        if part != "..":
            kept.append(part)
        elif kept:
            kept.pop()
        else:
            return None
    return "/".join(kept) or "."


def _form(path: str, fault: PathFault | None) -> str | None:
    """Give the form that names the place of a path, for repeats.

    Args:
        path: The path as written.
        fault: What `judge_path` found.

    Returns:
        The path itself without a fault, its normalized form when it has one,
        and `None` when it has no place inside the repository.
    """
    match fault:
        case None:
            return path
        case NotNormalized(normalized):
            return normalized
        case _:
            return None


def _words(path: str, fault: PathFault) -> str:
    """Word a fault as the module says.

    Args:
        path: The path as written.
        fault: What is wrong with it.

    Returns:
        "`<path>` <rule>", and "; use `<normalized>`" when there is a form, as a
        sentence.
    """
    match fault:
        case Unusable(rule):
            return f"`{path}` {rule}."
        case NotNormalized(normalized):
            return f"`{path}` is not normalized; use `{normalized}`."


def _fault(where: str, path: str, fault: PathFault, sentence: str) -> Diagnostic:
    """Build the error of a path with a fault and the sentence of its check.

    Args:
        where: The key path.
        path: The path as written.
        fault: What is wrong with it.
        sentence: What the check says about the key.

    Returns:
        The diagnostic.
    """
    return _error(where, f"{_words(path, fault)} {sentence}")


def _root_path(
    where: str, path: str, fault: PathFault | None, inputs: CheckInputs
) -> Diagnostic | None:
    """Judge one path of a root that is not a repeat.

    Args:
        where: The key path.
        path: The path as written.
        fault: What `judge_path` found.
        inputs: The repository root and the port that tells whether it exists.

    Returns:
        The error of a fault, a warning for a valid path that does not exist yet,
        and `None` for a path that exists.
    """
    if fault is not None:
        return _error(where, _words(path, fault))
    if inputs.files.exists(inputs.root / path):
        return None
    return Diagnostic("warning", where, f"`{path}` does not exist yet.")


def _found(skill: str, searched: Sequence[str], inputs: CheckInputs) -> bool:
    """Tell whether a skill has a `SKILL.md` in one of the directories.

    Args:
        skill: The skill's name.
        searched: The directories, relative to the repository root.
        inputs: The repository root and the port that tells whether it exists.

    Returns:
        False for a name that is empty, is `.` or `..` or has a `/`, without a
        lookup; otherwise whether a directory has `<skill>/SKILL.md`.
    """
    if skill in {"", ".", ".."} or "/" in skill:
        return False
    return any(
        inputs.files.exists(inputs.root / directory / skill / _SKILL_FILE)
        for directory in searched
    )


def _missing_skill(stage: str, skill: str, searched: Sequence[str]) -> Diagnostic:
    """Build the error of a skill that is not found.

    Args:
        stage: The stage's name.
        skill: The skill's name.
        searched: The directories looked in, in order.

    Returns:
        The diagnostic, at the stage's `skill`.
    """
    listed = and_list([f"`{directory}`" for directory in searched])
    message = (
        f"skill `{skill}` is not found in {listed}, searched in that order; "
        "the user's home is not searched."
    )
    return _error(join_path(join_path("stages", stage), "skill"), message)
