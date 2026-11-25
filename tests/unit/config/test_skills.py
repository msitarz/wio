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
from wio.errors import ConfigurationError
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


class _Refusing:
    """Settings that refuse the config."""

    def load(self) -> Config:
        """Refuse.

        Raises:
            ConfigurationError: Always.
        """
        message = "refused"
        raise ConfigurationError(message)


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
        (("a", "b"), ("b",), "b/wio-define"),
        (("./x", "b"), ("b",), "b/wio-define"),
        (("~/x",), ("~/x",), "~/x/wio-define"),
    ],
    ids=[
        "configured",
        "in-their-order",
        "agents",
        "claude",
        "the-root",
        "the-second",
        "after-a-faulty-one",
        "a-tilde-is-a-name",
    ],
)
def test_the_first_match_wins_in_the_documented_order(
    paths: tuple[str, ...], present: tuple[str, ...], expected: str
) -> None:
    """AC-1, AC-4: `[skills] paths`, then the two default directories."""
    # Given the skill in the directories
    files = _tree({str(Path(d, "wio-define", "SKILL.md")): d for d in present})

    # When it is looked up
    found = _find(files, paths=paths)

    # Then the first directory in the order is given, relative to the root, with
    # the hash of its own file
    own = expected.removesuffix("wio-define").rstrip("/") or "."
    assert found == FoundSkill(expected, _sha(f"SKILL.md\0{own}\0".encode()))


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
        ("wio-define", ("",), "wio-define/SKILL.md"),
        ("wio-define", ("/abs",), "/abs/wio-define/SKILL.md"),
        ("wio-define", ("../out",), "../out/wio-define/SKILL.md"),
        ("wio-define", (), "wio-define/SKILL.md"),
        ("wio-define", (), "skills/wio-define/SKILL.md"),
        ("wio-define", (), ".agents/wio/skills/wio-define/SKILL.md"),
    ],
    ids=[
        "no-skill-file",
        "not-normalized-path",
        "dot-dot",
        "slash",
        "empty",
        "dot",
        "empty-path",
        "absolute-path",
        "escaping-path",
        "the-root-unasked",
        "skills-unasked",
        "wio-skills-unasked",
    ],
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


@pytest.mark.parametrize(
    "name",
    [".hidden", "a b", "a\\b", " padded "],
    ids=["hidden", "space", "backslash", "padded"],
)
def test_a_skill_with_an_unusual_name_is_found(name: str) -> None:
    """AC-5: only the empty name, `.`, `..` and `/` are refused."""
    # Given a skill whose name is unusual
    files = _tree({f".agents/skills/{name}/SKILL.md": "x"})
    config = Config(stages=freeze({"s": Stage(skill=name)}))

    # When the config is checked and the skill is looked up
    errors = list(check_skills(config, CheckInputs(ROOT, files)))
    found = _find(files, name)

    # Then the check accepts it, and it is found under its name as written
    assert errors == []
    assert found is not None
    assert found.directory == f".agents/skills/{name}"


@pytest.mark.parametrize("name", ["..", ""], ids=["dot-dot", "empty"])
def test_the_settings_are_read_before_the_name_is_judged(name: str) -> None:
    """AC-2: settings that refuse end the lookup of any name."""
    # Given settings that refuse the config
    refusing = RepositorySkills(FakeRepository(), _tree({}), _Refusing())

    # When a name that is no skill name is looked up
    # Then the refusal is raised and not answered with `None`
    with pytest.raises(ConfigurationError):
        refusing.find_skill(name)


@pytest.mark.parametrize("fault", ["unreadable-file", "unlistable-directory"])
def test_what_cannot_be_read_is_not_left_out(fault: str) -> None:
    """AC-3, C-1: the hash never depends on what permissions let through."""
    # Given a skill with a file that cannot be read, or a directory that cannot
    # be listed
    files = _tree({f"{_SKILL}/SKILL.md": "s", f"{_SKILL}/sub/f": "f"})
    if fault == "unreadable-file":
        files.broken[ROOT / _SKILL / "sub" / "f"] = PermissionError(13, "denied")
    else:
        files.closed.add(ROOT / _SKILL / "sub")

    # When it is looked up
    # Then the failure is raised
    with pytest.raises(PermissionError):
        _find(files)


def test_the_whole_of_a_long_file_and_a_name_as_written_are_hashed() -> None:
    """AC-3: nothing is cut off or normalized."""
    # Given a long file that ends in NUL bytes, and a name with a combining mark
    text = "x" * 200_000 + "\0\0"
    files = _tree({f"{_SKILL}/SKILL.md": text, f"{_SKILL}/e\u0301": "e"})

    # When the skill is looked up
    found = _find(files)

    # Then all of both is hashed
    assert found is not None
    assert found.files_hash == _sha(b"SKILL.md\0" + text.encode() + b"\0e\xcc\x81\0e\0")


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


def test_every_file_counts_whatever_its_name_depth_or_size() -> None:
    """AC-3, A-3: hidden, tool-made, empty and deep files too."""
    # Given a skill with files that a tool might think it can skip
    names = [
        ".DS_Store",
        ".d/f",
        ".env",
        ".git/HEAD",
        "SKILL.md",
        "__pycache__/m.pyc",
        "a/b/c/d",
        "empty",
        "node_modules/p",
    ]
    files = _tree({f"{_SKILL}/{n}": "" if n == "empty" else "x" for n in names})

    # When it is looked up
    found = _find(files)

    # Then each is hashed
    expected = b"".join(
        n.encode() + (b"\0\0" if n == "empty" else b"\0x\0") for n in names
    )
    assert found is not None
    assert found.files_hash == _sha(expected)


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
    # Given stages whose skills are in each default directory, one whose skill
    # is a directory without `SKILL.md` and one whose skill exists nowhere
    files = _tree(
        {
            f"{_SKILL}/SKILL.md": "x",
            ".claude/skills/other/SKILL.md": "x",
            ".agents/skills/bare/notes.md": "n",
        }
    )
    stages = {
        "here": Stage(skill="wio-define"),
        "there": Stage(skill="other"),
        "bare": Stage(skill="bare"),
        "gone": Stage(skill="ghost"),
    }
    config = Config(stages=freeze(stages))

    # When the config is checked and each skill is looked up
    errors = [d.where for d in check_skills(config, CheckInputs(ROOT, files))]
    found = {name: _find(files, str(s.skill)) for name, s in stages.items()}

    # Then the check reports the last two, and only the first two are found
    assert errors == ["stages.bare.skill", "stages.gone.skill"]
    assert [name for name, skill in found.items() if skill] == ["here", "there"]
