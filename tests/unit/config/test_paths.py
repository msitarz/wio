# SPDX-License-Identifier: Apache-2.0
"""Tests of the checks of paths, skills and templates."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.unit.config.fakes import (
    ROOT,
    MemoryFileSystem,
    diagnostic_lines,
    make_config,
)
from wio.config import CheckInputs, paths
from wio.models.config import Root, Skills, Stage, Templates, Works
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.models.config import Config


_HOME_SKILL = Path("/home/user/.claude/skills/c/SKILL.md")


def _inputs(*present: str) -> CheckInputs:
    """Build the inputs of a check over a file system that holds some paths.

    Args:
        *present: The paths, relative to the repository root, that exist.

    Returns:
        The inputs; a directory exists when the file system holds a key for it.
    """
    return CheckInputs(ROOT, MemoryFileSystem({ROOT / path: "" for path in present}))


def _roots(**paths_of: Sequence[str]) -> Config:
    """Build a config whose roots have the paths given.

    Args:
        **paths_of: Each root's name mapped to its paths.

    Returns:
        The config.
    """
    roots = {name: Root(paths=tuple(found)) for name, found in paths_of.items()}
    return make_config(roots=roots)


def test_a_fault_is_worded_with_its_rule_and_its_normalized_form() -> None:
    """AC-1: "`<path>` <rule>", and "; use `<normalized>`" only when there is one."""
    # Given the paths `src/` and `../x`
    config = _roots(a=["src/", "../x"])

    # When their faults are worded in the root path check
    found = diagnostic_lines(paths.check_root_paths(config, _inputs()))

    # Then the first says "`src/` is not normalized; use `src`", and the second
    # says "`../x` leaves the repository" and names no form
    assert found == [
        "error: roots.a.paths[0]: `src/` is not normalized; use `src`.",
        "error: roots.a.paths[1]: `../x` leaves the repository.",
    ]


@pytest.mark.parametrize(
    ("path", "fault"),
    [
        ("src", None),
        (".", None),
        ("a/b", None),
        ("src/", paths.NotNormalized("src")),
        ("a/./b", paths.NotNormalized("a/b")),
        ("a/../b", paths.NotNormalized("b")),
        ("src//x", paths.NotNormalized("src/x")),
        ("./", paths.NotNormalized(".")),
        ("a/..", paths.NotNormalized(".")),
        ("../x", paths.Unusable("leaves the repository")),
        ("a/../../x", paths.Unusable("leaves the repository")),
        ("/abs", paths.Unusable("is absolute")),
        ("", paths.Unusable("is empty")),
    ],
)
def test_a_path_is_judged_as_text_and_gets_its_normalized_form(
    path: str, fault: paths.PathFault | None
) -> None:
    """AC-1: the first fault that applies, and the form that names the same place."""
    # Given a path as the config writes it

    # When it is judged
    found = paths.judge_path(path)

    # Then a normalized path has no fault, and any other has the first fault of
    # the order, with the normalized form only when it is not normalized
    assert found == fault


def test_root_paths_not_normalized_or_outside_the_repository_are_errors() -> None:
    """AC-1: each error names the rule and the normalized form where one exists."""
    # Given a root `a` with paths `src/`, `../x`, `/abs` and `a/./b`
    config = _roots(a=["src/", "../x", "/abs", "a/./b"])

    # When the root paths are checked
    found = diagnostic_lines(paths.check_root_paths(config, _inputs()))

    # Then each is an error at its path that names the rule and the normalized form
    assert found == [
        "error: roots.a.paths[0]: `src/` is not normalized; use `src`.",
        "error: roots.a.paths[1]: `../x` leaves the repository.",
        "error: roots.a.paths[2]: `/abs` is absolute.",
        "error: roots.a.paths[3]: `a/./b` is not normalized; use `a/b`.",
    ]


def test_a_repeated_root_path_is_judged_on_its_normalized_text() -> None:
    """AC-1: the error names the first occurrence, and two roots may share a path."""
    # Given a root `b` with `src` twice and `src/` a third time, and a root `c`
    # with `src`
    config = _roots(b=["src", "src", "src/"], c=["src"])

    # When the root paths are checked
    found = diagnostic_lines(paths.check_root_paths(config, _inputs("src")))

    # Then each later path of `b` has one error that names the index of the first
    # and not its fault, and the root `c` has none
    assert found == [
        "error: roots.b.paths[1]: `src` repeats the path at `roots.b.paths[0]`.",
        "error: roots.b.paths[2]: `src/` repeats the path at `roots.b.paths[0]`.",
    ]


def test_a_path_repeats_one_that_has_a_fault_by_its_normalized_form() -> None:
    """AC-1: fixing the first path does not reveal a repeat on the next run."""
    # Given a root with `src/` and then `src`
    config = _roots(a=["src/", "src"])

    # When the root paths are checked
    found = diagnostic_lines(paths.check_root_paths(config, _inputs("src")))

    # Then the first is a fault and the second names it as the path it repeats
    assert found == [
        "error: roots.a.paths[0]: `src/` is not normalized; use `src`.",
        "error: roots.a.paths[1]: `src` repeats the path at `roots.a.paths[0]`.",
    ]


def test_a_missing_root_path_is_a_warning_and_a_faulty_one_is_not_asked_about() -> None:
    """AC-1: only a valid path is looked for below the repository root."""
    # Given a root path `docs/new` that does not exist, one that exists, a repeat
    # of the first, and an absolute path; a directory exists when the fake file
    # system holds a key for it
    config = _roots(a=["docs/new", "src", "docs/new", "/abs"])

    # When the root paths are checked
    found = diagnostic_lines(paths.check_root_paths(config, _inputs("src")))

    # Then the first is a warning, the second has none, the repeat only its
    # error, and the absolute path only its error
    assert found == [
        "warning: roots.a.paths[0]: `docs/new` does not exist yet.",
        "error: roots.a.paths[2]: `docs/new` repeats the path at `roots.a.paths[0]`.",
        "error: roots.a.paths[3]: `/abs` is absolute.",
    ]


def _skill_config(
    *names: str, directories: Sequence[str] = (), goal: str | None = None
) -> Config:
    """Build a config with stages that name skills.

    Args:
        *names: The skills the stages `s0`, `s1` and so on name.
        directories: The value of `[skills] paths`.
        goal: The goal of every stage, which makes it a stage with a goal.

    Returns:
        The config.
    """
    stages = {f"s{i}": Stage(skill=name, goal=goal) for i, name in enumerate(names)}
    return make_config(stages=stages, skills=Skills(paths=tuple(directories)))


def test_a_skill_is_found_in_the_searched_directories_in_order() -> None:
    """AC-2: `skills.paths`, then `.agents/skills`, then `.claude/skills`."""
    # Given skills `a` in `.claude/skills` and `b` in a configured path, `d` in
    # `.agents/skills`, and a stage with a goal naming a missing skill
    inputs = _inputs(
        ".claude/skills/a/SKILL.md", "extra/b/SKILL.md", ".agents/skills/d/SKILL.md"
    )
    found = make_config(
        stages={
            "x": Stage(skill="a"),
            "y": Stage(skill="b"),
            "z": Stage(skill="d"),
            "w": Stage(goal="g", skill="missing"),
        },
        skills=Skills(paths=("extra",)),
    )

    # When the skills are checked
    result = list(paths.check_skills(found, inputs))

    # Then `a`, `b` and `d` pass and the stage with a goal is not judged
    assert result == []


def test_a_skill_that_is_not_found_lists_where_wio_looked() -> None:
    """AC-2: the directories in order, and that the user's home is not searched."""
    # Given a stage naming `c`, which exists only in the user's home, and stages
    # whose skill names are empty, `..` and `a/b`
    config = _skill_config("c", "", "..", "a/b", directories=["extra"])
    inputs = CheckInputs(ROOT, MemoryFileSystem({_HOME_SKILL: ""}))

    # When the skills are checked
    found = diagnostic_lines(paths.check_skills(config, inputs))

    # Then an error at `stages.<name>.skill` lists the directories, once each as
    # relative paths, and says the user's home is not searched; the odd names are
    # not found without a lookup
    listed = "`extra`, `.agents/skills` and `.claude/skills`"
    assert found == [
        f"error: stages.s{i}.skill: skill `{name}` is not found in {listed}, "
        "searched in that order; the user's home is not searched."
        for i, name in enumerate(["c", "", "..", "a/b"])
    ]


def test_a_skill_path_outside_the_repository_is_an_error_and_not_searched() -> None:
    """AC-2: a skill path follows the rule of a root path."""
    # Given `[skills] paths = ["../skills", "../skills", "skills/", ".claude/skills"]`
    # and a skill that only the path outside the repository would hold
    config = _skill_config(
        "a", directories=["../skills", "../skills", "skills/", ".claude/skills"]
    )

    # When the skills are checked
    found = diagnostic_lines(paths.check_skills(config, _inputs("skills/a/SKILL.md")))

    # Then an error at `skills.paths[0]` and one at `skills.paths[1]` say "The path
    # must stay inside the repository.", no repeat is reported, and the
    # directories listed for a missing skill leave them out and list a directory
    # once
    sentence = "The path must stay inside the repository."
    unnormalized = "`skills/` is not normalized; use `skills`."
    assert found[:3] == [
        f"error: skills.paths[0]: `../skills` leaves the repository. {sentence}",
        f"error: skills.paths[1]: `../skills` leaves the repository. {sentence}",
        f"error: skills.paths[2]: {unnormalized} {sentence}",
    ]
    assert found[3].endswith(
        "is not found in `.claude/skills` and `.agents/skills`, searched in that "
        "order; the user's home is not searched."
    )


def test_the_templates_table_needs_a_valid_dir_and_non_empty_template_names() -> None:
    """AC-3: each error names the key path and what a valid value is."""
    # Given `[templates] dir = "../t"` and a kind whose template name is empty
    templates = Templates(dir="../t", kinds=freeze({"feature": "", "a.b": ""}))
    config = make_config(templates=templates)

    # When the templates are checked
    found = diagnostic_lines(paths.check_templates(config, _inputs()))

    # Then the first ends with "A templates directory is a normalized path inside
    # the repository." and the second at `templates.kinds.<kind>` says the
    # template name is empty
    empty = (
        "the template name is empty; a kind names a template with a non-empty string."
    )
    directory = (
        "error: templates.dir: `../t` leaves the repository. A templates directory "
        "is a normalized path inside the repository."
    )
    assert found == [
        directory,
        f"error: templates.kinds.feature: {empty}",
        f'error: templates.kinds."a.b": {empty}',
    ]


def test_no_templates_table_gets_no_diagnostic() -> None:
    """AC-3: the defaults are valid."""
    # Given a config without a `[templates]` table
    config = make_config()

    # When the templates are checked
    found = list(paths.check_templates(config, _inputs()))

    # Then no diagnostic is returned
    assert found == []


@pytest.mark.parametrize(
    ("path", "words"),
    [
        ("/abs", "`/abs` is absolute."),
        ("", "`` is empty."),
        ("works/", "`works/` is not normalized; use `works`."),
    ],
)
def test_a_works_dir_outside_the_repository_is_an_error(path: str, words: str) -> None:
    """AC-4: the directory is a normalized path inside the repository."""
    # Given `[works] dir` set to `path`
    config = make_config(works=Works(dir=path))

    # When the Works directory is checked
    found = diagnostic_lines(paths.check_works_dir(config, _inputs()))

    # Then an error at `works.dir` ends with "The path must be inside the
    # repository."
    assert found == [
        f"error: works.dir: {words} The path must be inside the repository."
    ]


def test_a_stage_with_both_a_goal_and_a_skill_is_left_to_the_shape() -> None:
    """AC-2: only a stage with a skill and no goal is looked up."""
    # Given a stage with a goal and a skill that is nowhere
    config = _skill_config("nowhere", goal="a goal")

    # When the skills are checked
    found = list(paths.check_skills(config, _inputs()))

    # Then no diagnostic is returned
    assert found == []
