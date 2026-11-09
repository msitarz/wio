# SPDX-License-Identifier: Apache-2.0
"""Fakes of the ports the loader reads through, for the tests of `wio.config`."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from wio.config import CHECKS, load_config
from wio.models.config import Config, Gates, Skills, Templates, Works
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.config import Check, Loaded
    from wio.models.config import Action, Root, Stage

ROOT = Path("/repo")
CONFIG = ROOT / ".agents" / "wio" / "config.toml"


@dataclass
class MemoryFileSystem:
    """A `FileSystem` over a dictionary of paths to text.

    Only what the loader reads exists; a path that is not a key is missing.
    """

    files: dict[Path, str] = field(default_factory=dict)
    failure: Exception | None = None

    def read_text(self, path: Path) -> str:
        """Read a file of the dictionary.

        Args:
            path: The file to read.

        Returns:
            Its text.

        Raises:
            FileNotFoundError: The path is not a key.
            Exception: The `failure` the fake was given, whatever the path.
        """
        if self.failure is not None:
            raise self.failure
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def read_bytes(self, path: Path) -> bytes:
        """Read a file of the dictionary as bytes.

        Args:
            path: The file to read.

        Returns:
            Its text, encoded.
        """
        return self.read_text(path).encode("utf-8")

    def write_text(self, path: Path, text: str) -> None:
        """Store a text.

        Args:
            path: The file to write.
            text: Its content.
        """
        self.files[path] = text

    def append_text(self, path: Path, text: str) -> None:
        """Append a text.

        Args:
            path: The file to append to.
            text: What to add.
        """
        self.files[path] = self.files.get(path, "") + text

    def exists(self, path: Path) -> bool:
        """Tell whether a file is stored.

        Args:
            path: Any path.

        Returns:
            True when the path is a key.
        """
        return path in self.files

    def is_dir(self, path: Path) -> bool:  # noqa: ARG002
        """Tell that nothing is a directory.

        Args:
            path: Any path.

        Returns:
            False.
        """
        return False

    def is_file(self, path: Path) -> bool:
        """Tell whether a file is stored.

        Args:
            path: Any path.

        Returns:
            True when the path is a key.
        """
        return self.exists(path)

    def list_dir(self, path: Path) -> Sequence[Path]:
        """List the stored files directly under a path.

        Args:
            path: The directory.

        Returns:
            The stored files whose parent is the path, sorted.
        """
        return sorted(p for p in self.files if p.parent == path)


@dataclass
class FakeRepository:
    """A `Repository` whose root is fixed, or that is not inside a repository."""

    top: Path | None = ROOT
    message: str = "not inside a git repository: /elsewhere"

    def root(self) -> Path:
        """Find the root.

        Returns:
            The fixed root.

        Raises:
            RuntimeError: The fake is outside any repository.
        """
        if self.top is None:
            raise RuntimeError(self.message)
        return self.top

    def identity(self) -> Path:
        """Find the identity, which is the root's own `.git`.

        Returns:
            The path of the `.git` directory.
        """
        return self.root() / ".git"

    def show_index(self, path: Path) -> str | None:  # noqa: ARG002
        """Read a staged file; nothing is staged.

        Args:
            path: The file.

        Returns:
            None.
        """
        return None

    def is_dirty(self) -> bool:
        """Tell whether the tree is dirty; it never is.

        Returns:
            False.
        """
        return False


def load_text(text: str, checks: Sequence[Check] = ()) -> Loaded:
    """Run the loader on a config text kept in memory.

    Args:
        text: The content of `.agents/wio/config.toml`.
        checks: The checks to run after the shape.

    Returns:
        What the loader found.
    """
    return load_config(
        FakeRepository(), MemoryFileSystem({CONFIG: text}), checks=checks
    )


def run_order(ours: Sequence[Check]) -> list[Check]:
    """List some checks in the order the check run runs them.

    Args:
        ours: The checks of one Work.

    Returns:
        Those of `ours` that `wio.config.CHECKS` holds, in the order it holds
        them, so a test says that its Work's checks run in a stated order whatever
        the other Works append.
    """
    return [check for check in CHECKS if check in ours]


def make_config(
    *,
    stages: Mapping[str, Stage] | None = None,
    stage_presets: Mapping[str, tuple[str, ...]] | None = None,
    actions: Mapping[str, Action] | None = None,
    roots: Mapping[str, Root] | None = None,
    works: Works | None = None,
    gates: Gates | None = None,
    skills: Skills | None = None,
    templates: Templates | None = None,
) -> Config:
    """Build a `Config` from the plain mappings a test writes.

    Args:
        stages: The stages by name.
        stage_presets: The stages of each stage preset.
        actions: The actions by name.
        roots: The roots by name.
        works: The `works` table.
        gates: The `gates` table.
        skills: The `skills` table.
        templates: The `templates` table.

    Returns:
        The config, with the defaults for what is not given.
    """
    return Config(
        stages=freeze(stages or {}),
        stage_presets=freeze(stage_presets or {}),
        actions=freeze(actions or {}),
        roots=freeze(roots or {}),
        works=works or Works(),
        gates=gates or Gates(),
        skills=skills or Skills(),
        templates=templates or Templates(),
    )
