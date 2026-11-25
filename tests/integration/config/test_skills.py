# SPDX-License-Identifier: Apache-2.0
"""Tests of the lookup of a skill on a real disk and a real repository."""

import hashlib
import os
from typing import TYPE_CHECKING, override

import pytest

from tests.support import enter, git
from wio.config.settings import ConfigSettings
from wio.config.skills import RepositorySkills
from wio.env.adapters import ProcessEnvironment
from wio.errors import ConfigurationError
from wio.io import adapters
from wio.models.config import Config

if TYPE_CHECKING:
    from pathlib import Path

    from tests.sandbox import Sandbox


class _RegularOnly(adapters.LocalFileSystem):
    """A disk that fails, and does not block, on a read of what is not a file."""

    @override
    def read_bytes(self, path: Path) -> bytes:
        """Read a regular file.

        Args:
            path: The file.

        Returns:
            Its bytes.
        """
        assert path.is_file(), f"read of {path}, which is not a regular file"
        return super().read_bytes(path)


class _Settings:
    """Settings that give the config of an empty file."""

    def load(self) -> Config:
        """Give the config.

        Returns:
            The default config.
        """
        return Config()


def _lookup(settings: ConfigSettings | None = None) -> RepositorySkills:
    """Build the lookup with the real adapters.

    Args:
        settings: The settings; those of an empty config by default.

    Returns:
        The lookup of the repository of the working directory.
    """
    return RepositorySkills(
        adapters.GitRepository(ProcessEnvironment()),
        _RegularOnly(),
        settings or _Settings(),
    )


def _write(path: Path, text: str) -> None:
    """Write a file and its parents.

    Args:
        path: The file.
        text: Its content.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _hash() -> str:
    """Look the skill `wio-define` up for its hash.

    Returns:
        The files hash.
    """
    found = _lookup().find_skill("wio-define")
    assert found is not None
    return found.files_hash


@pytest.mark.slow
def test_the_hash_changes_with_the_files_and_only_with_them(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3, C-1: bytes and names count; links, times and modes do not."""
    # Given a repository with a skill of two texts and a file that is not text
    git(sandbox, "init", "-q", check=True)
    skill = sandbox.root / ".agents" / "skills" / "wio-define"
    _write(skill / "SKILL.md", "x\n")
    _write(skill / "references" / "a.md", "y\n")
    (skill / "logo.bin").write_bytes(b"\xff\x00\r\n")
    enter(sandbox, monkeypatch)
    hashes = [_hash()]

    # When a byte changes, a file is added, a file is renamed, a link is added,
    # and then a time and a mode change
    _write(skill / "references" / "a.md", "z\n")
    hashes.append(_hash())
    _write(skill / "b.md", "b\n")
    hashes.append(_hash())
    (skill / "b.md").rename(skill / "c.md")
    hashes.append(_hash())
    (skill / "link.md").symlink_to(skill / "c.md")
    hashes.append(_hash())
    os.utime(skill / "SKILL.md", (0, 0))
    (skill / "SKILL.md").chmod(0o755)
    hashes.append(_hash())

    # Then the first three changes give a new hash, and the last two do not
    assert len(set(hashes[:4])) == 4
    assert hashes[3:] == [hashes[3]] * 3


@pytest.mark.slow
def test_the_directory_is_relative_to_the_repository_from_anywhere_in_it(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: the working directory does not change the answer."""
    # Given a repository with a skill, and another working directory in it
    git(sandbox, "init", "-q", check=True)
    _write(sandbox.root / ".agents" / "skills" / "wio-define" / "SKILL.md", "x")
    sub = sandbox.root / "sub"
    sub.mkdir()
    enter(sandbox, monkeypatch)
    monkeypatch.chdir(sub)

    # When the skill is looked up
    found = _lookup().find_skill("wio-define")

    # Then the directory is relative to the root
    assert found is not None
    assert found.directory == ".agents/skills/wio-define"


@pytest.mark.slow
def test_a_skill_in_the_home_directory_is_not_found(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2: the home is never searched."""
    # Given a skill in the user's home only, and a directory of the repository
    # with no `SKILL.md`
    git(sandbox, "init", "-q", check=True)
    home = sandbox.root.parent / "home"
    for directory in (".agents", ".claude"):
        _write(home / directory / "skills" / "wio-define" / "SKILL.md", "x")
    (sandbox.root / ".agents" / "skills" / "wio-define").mkdir(parents=True)
    enter(sandbox, monkeypatch)
    monkeypatch.setenv("HOME", str(home))

    # When the skill is looked up
    found = _lookup().find_skill("wio-define")

    # Then there is none
    assert found is None


@pytest.mark.slow
def test_a_linked_skill_directory_has_the_files_of_its_target(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: only links below the skill's directory are left out."""
    # Given a skill in `.agents/skills` and a link to it that is searched first
    git(sandbox, "init", "-q", check=True)
    target = sandbox.root / "shared" / "wio-define"
    _write(target / "SKILL.md", "x\n")
    linked = sandbox.root / ".agents" / "skills" / "wio-define"
    linked.parent.mkdir(parents=True)
    linked.symlink_to(target, target_is_directory=True)
    enter(sandbox, monkeypatch)

    # When it is looked up
    found = _lookup().find_skill("wio-define")

    # Then the link is the directory, and the target's file is hashed
    assert found is not None
    assert found.directory == ".agents/skills/wio-define"
    assert found.files_hash == hashlib.sha256(b"SKILL.md\0x\n\0").hexdigest()


@pytest.mark.slow
def test_a_skill_file_that_the_check_accepts_is_found(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5: the check asks only that `SKILL.md` exists."""
    # Given a skill whose `SKILL.md` is a directory, which the check accepts
    git(sandbox, "init", "-q", check=True)
    skill = sandbox.root / ".agents" / "skills" / "wio-define"
    (skill / "SKILL.md").mkdir(parents=True)
    enter(sandbox, monkeypatch)

    # When it is looked up
    found = _lookup().find_skill("wio-define")

    # Then it is found
    assert found is not None


@pytest.mark.slow
def test_an_entry_that_is_not_a_regular_file_adds_nothing(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: only regular files are read."""
    # Given a skill that holds a named pipe, which a read would block on, and a
    # disk that fails instead
    git(sandbox, "init", "-q", check=True)
    skill = sandbox.root / ".agents" / "skills" / "wio-define"
    _write(skill / "SKILL.md", "x\n")
    os.mkfifo(skill / "pipe")
    enter(sandbox, monkeypatch)

    # When it is looked up
    found = _hash()

    # Then only the regular file is hashed
    assert found == hashlib.sha256(b"SKILL.md\0x\n\0").hexdigest()


@pytest.mark.slow
def test_the_bytes_of_a_file_are_hashed_as_they_are_stored(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: no decoding and no change of line ends."""
    # Given a skill with a file that is not text and has a CRLF line end
    git(sandbox, "init", "-q", check=True)
    skill = sandbox.root / ".agents" / "skills" / "wio-define"
    _write(skill / "SKILL.md", "x\n")
    (skill / "logo.bin").write_bytes(b"\xff\x00\r\n")
    enter(sandbox, monkeypatch)

    # When it is looked up
    found = _hash()

    # Then the hash is of the stored bytes
    stored = b"SKILL.md\0x\n\0logo.bin\0\xff\x00\r\n\0"
    assert found == hashlib.sha256(stored).hexdigest()


@pytest.mark.slow
def test_settings_that_refuse_the_config_end_the_lookup(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2: the real settings give no config that has an error."""
    # Given a skill under a path that the config writes with a fault
    git(sandbox, "init", "-q", check=True)
    _write(sandbox.root / "a" / "wio-define" / "SKILL.md", "x")
    config = sandbox.root / ".agents" / "wio" / "config.toml"
    _write(config, '[skills]\npaths = ["./a"]\n')
    enter(sandbox, monkeypatch)
    repository = adapters.GitRepository(ProcessEnvironment())
    settings = ConfigSettings(repository, adapters.LocalFileSystem())

    # When the skill is looked up with the real settings
    with pytest.raises(ConfigurationError) as caught:
        _lookup(settings).find_skill("wio-define")

    # Then the error names the faulty path
    assert "skills.paths[0]" in str(caught.value)
