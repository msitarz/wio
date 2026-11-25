# SPDX-License-Identifier: Apache-2.0
"""Tests of the lookup of a skill and of the hash of its files."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.unit.fakes import ROOT, FakeRepository, MemoryFileSystem
from wio.config.checks import CheckInputs
from wio.config.paths import check_skills
from wio.config.skills import RepositorySkills
from wio.models.config import Config, Skills, Stage
from wio.models.frozen import freeze
from wio.models.skill import FoundSkill

_SKILL = ".agents/skills/wio-define"


@dataclass
class _Settings:
    """Settings that give a config with `[skills] paths`.

    Attributes:
        paths: The value of `[skills] paths`.
    """

    paths: tuple[str, ...] = ()

    def load(self) -> Config:
        """Give the config.

        Returns:
            The config.
        """
        return Config(skills=Skills(paths=self.paths))


def _tree(files: dict[str, str], links: tuple[str, ...] = ()) -> MemoryFileSystem:
    """Build a repository on a fake disk.

    Args:
        files: The text of each file by its path below the root.
        links: The paths below the root that are symbolic links.

    Returns:
        The file system.
    """
    return MemoryFileSystem(
        {ROOT / path: text for path, text in files.items()},
        links={ROOT / path for path in links},
    )


def _find(
    files: MemoryFileSystem, name: str = "wio-define", paths: tuple[str, ...] = ()
) -> FoundSkill | None:
    """Look a skill up.

    Args:
        files: The disk.
        name: The skill's name.
        paths: The value of `[skills] paths`.

    Returns:
        What the lookup gives.
    """
    lookup = RepositorySkills(FakeRepository(), files, _Settings(paths))
    return lookup.find_skill(name)


def _sha(data: bytes) -> str:
    """Hash bytes as the lookup is to.

    Args:
        data: The bytes.

    Returns:
        The 64 hexadecimal digits.
    """
    return hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize(
    ("paths", "present", "expected"),
    [
        (
            (".agents/wio/skills",),
            (".agents/wio/skills", ".agents/skills"),
            ".agents/wio/skills/wio-define",
        ),
        (("b", "a"), ("a", "b"), "b/wio-define"),
        ((), (".claude/skills", ".agents/skills"), ".agents/skills/wio-define"),
        ((), (".claude/skills",), ".claude/skills/wio-define"),
        ((".",), (".",), "wio-define"),
    ],
    ids=["configured", "in-their-order", "agents", "claude", "the-root"],
)
def test_the_first_match_wins_in_the_documented_order(
    paths: tuple[str, ...], present: tuple[str, ...], expected: str
) -> None:
    """AC-1, AC-4: `[skills] paths`, then the two default directories."""
    # Given the skill in the directories
    files = _tree({str(Path(d, "wio-define", "SKILL.md")): "x" for d in present})

    # When it is looked up
    found = _find(files, paths=paths)

    # Then the first directory in the order is given, relative to the root
    assert found is not None
    assert found.directory == expected


def test_a_directory_without_the_skill_file_does_not_end_the_search() -> None:
    """AC-1: the default directories are searched after the configured ones."""
    # Given a configured directory whose `wio-define` has no `SKILL.md`, and the
    # skill in a default directory
    files = _tree({"a/wio-define/notes.md": "n", f"{_SKILL}/SKILL.md": "x"})

    # When it is looked up
    found = _find(files, paths=("a",))

    # Then the one in the default directory is found
    assert found is not None
    assert found.directory == _SKILL


@pytest.mark.parametrize(
    ("name", "paths", "path"),
    [
        ("wio-define", (), f"{_SKILL}/notes.md"),
        ("wio-define", ("./a",), "a/wio-define/SKILL.md"),
        ("..", (), ".agents/skills/../SKILL.md"),
        ("a/b", (), ".agents/skills/a/b/SKILL.md"),
        ("", (), ".agents/skills/SKILL.md"),
        (".", (), ".agents/skills/SKILL.md"),
    ],
    ids=["no-skill-file", "faulty-path", "dot-dot", "slash", "empty", "dot"],
)
def test_what_is_not_a_skill_is_not_found(
    name: str, paths: tuple[str, ...], path: str
) -> None:
    """AC-2: each way of not being a skill gives `None`."""
    # Given a file that a looser search would take for the skill
    files = _tree({path: "x"})

    # When the name is looked up
    found = _find(files, name, paths)

    # Then there is no skill
    assert found is None


def test_the_hash_is_of_the_paths_and_the_bytes() -> None:
    """AC-3: the bytes that the contract fixes."""
    # Given a skill with two files
    files = _tree({f"{_SKILL}/SKILL.md": "x\n", f"{_SKILL}/references/a.md": "y\n"})

    # When it is looked up
    found = _find(files)

    # Then it has the directory and the hash of the contract
    assert found == FoundSkill(
        _SKILL, "1a47c19b09044a025c5c5b147b88adffccd800023e4e1c1ee70c730329c16fe2"
    )


def test_the_files_are_hashed_in_the_order_of_their_path_bytes() -> None:
    """AC-3: not in the order that a walk of the tree meets them."""
    # Given files whose order by directory differs from their order by path
    files = _tree(
        {f"{_SKILL}/SKILL.md": "s", f"{_SKILL}/a/c": "1", f"{_SKILL}/a-b": "2"}
    )

    # When the skill is looked up
    found = _find(files)

    # Then `a-b` is hashed before `a/c`
    assert found is not None
    assert found.files_hash == _sha(b"SKILL.md\0s\0a-b\x002\0a/c\x001\0")


def test_names_are_hashed_and_ordered_as_their_bytes_on_disk() -> None:
    """AC-3: also a name that is not UTF-8."""
    # Given a name with the byte `ff`, which is not UTF-8, and a name whose
    # character comes after it as text and before it as bytes
    files = _tree(
        {
            f"{_SKILL}/SKILL.md": "s",
            f"{_SKILL}/\udcff": "1",
            f"{_SKILL}/\U00010000": "2",
        }
    )

    # When the skill is looked up
    found = _find(files)

    # Then the bytes of each name are hashed, in the order of those bytes
    assert found is not None
    assert found.files_hash == _sha(b"SKILL.md\0s\0\xf0\x90\x80\x80\x002\0\xff\x001\0")


def test_a_skill_under_a_faulty_path_is_reported_and_not_found() -> None:
    """AC-2: the check reports the path that the lookup leaves out."""
    # Given a skill under a path that is not normalized
    files = _tree({"a/wio-define/SKILL.md": "x"})
    config = Config(skills=Skills(paths=("./a",)))

    # When the config is checked and the skill is looked up
    errors = [d.where for d in check_skills(config, CheckInputs(ROOT, files))]
    found = _find(files, paths=("./a",))

    # Then the path is reported and there is no skill
    assert errors == ["skills.paths[0]"]
    assert found is None


def test_hidden_files_and_directories_count() -> None:
    """AC-3: every file, whatever its name."""
    # Given a skill with a hidden file and a file in a hidden directory
    files = _tree(
        {f"{_SKILL}/SKILL.md": "s", f"{_SKILL}/.env": "e", f"{_SKILL}/.d/f": "f"}
    )

    # When it is looked up
    found = _find(files)

    # Then both are hashed
    assert found is not None
    assert found.files_hash == _sha(b".d/f\0f\0.env\0e\0SKILL.md\0s\0")


def test_a_symbolic_link_adds_nothing() -> None:
    """AC-3: a link to a file, to a directory and as `SKILL.md`."""
    # Given a skill whose `SKILL.md`, one file and one directory are links
    files = _tree(
        {
            f"{_SKILL}/SKILL.md": "s",
            f"{_SKILL}/kept": "k",
            f"{_SKILL}/linked-file": "f",
            f"{_SKILL}/linked-dir/inside": "i",
        },
        links=(
            f"{_SKILL}/SKILL.md",
            f"{_SKILL}/linked-file",
            f"{_SKILL}/linked-dir",
        ),
    )

    # When it is looked up
    found = _find(files)

    # Then it is found, and only the regular file counts
    assert found == FoundSkill(_SKILL, _sha(b"kept\0k\0"))


def test_the_lookup_and_the_check_agree() -> None:
    """AC-5: found exactly when `wio config check` accepts the skill."""
    # Given a stage whose skill exists and one whose skill exists nowhere
    files = _tree({f"{_SKILL}/SKILL.md": "x"})
    stages = {"here": Stage(skill="wio-define"), "gone": Stage(skill="ghost")}
    config = Config(stages=freeze(stages))

    # When the config is checked and each skill is looked up
    errors = [d.where for d in check_skills(config, CheckInputs(ROOT, files))]
    found = {name: _find(files, str(s.skill)) for name, s in stages.items()}

    # Then the check reports only the second, and only the first is found
    assert errors == ["stages.gone.skill"]
    assert found["here"] is not None
    assert found["gone"] is None
