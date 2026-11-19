# SPDX-License-Identifier: Apache-2.0
"""Fakes of the ports that the unit tests of several components share."""

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

from tests.fakes import value_or_raise

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.commits import Commit
    from wio.models.events import Event

ROOT = Path("/repo")


@dataclass
class MemoryFileSystem:
    """A `FileSystem` over a dictionary of paths to text.

    Only what the loader reads exists; a path that is not a key is missing.
    """

    files: dict[Path, str] = field(default_factory=dict)
    links: set[Path] = field(default_factory=set)
    broken: dict[Path, Exception] = field(default_factory=dict)
    failure: Exception | None = None
    calls: list[tuple[str, Path]] = field(default_factory=list)

    appends: list[tuple[Path, str]] = field(default_factory=list)
    append_failure: Exception | None = None

    def read_text(self, path: Path) -> str:
        """Read a file of the dictionary.

        Args:
            path: The file to read.

        Returns:
            Its text.

        Raises:
            FileNotFoundError: The path is not a key.
            Exception: The `failure` the fake was given, whatever the path, or the
                one it was given for this path in `broken`.
        """
        self.calls.append(("read_text", path))
        if self.failure is not None:
            raise self.failure
        if path in self.broken:
            raise self.broken[path]
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
        self.calls.append(("write_text", path))
        self.files[path] = text

    def append_text(self, path: Path, text: str) -> None:
        """Append a text.

        Args:
            path: The file to append to.
            text: What to add.

        Raises:
            Exception: The configured append failure, before storing the text.
        """
        self.calls.append(("append_text", path))
        self.appends.append((path, text))
        if self.append_failure is not None:
            raise self.append_failure
        self.files[path] = self.files.get(path, "") + text

    def exists(self, path: Path) -> bool:
        """Tell whether a file or a directory that holds one is stored.

        Args:
            path: Any path.

        Returns:
            True when the path is a key or holds one.
        """
        return path in self.files or any(path in key.parents for key in self.files)

    def is_dir(self, path: Path) -> bool:
        """Tell whether a stored file lies below a path.

        Args:
            path: Any path.

        Returns:
            True when the path is the parent, at any depth, of a key, so a
            directory is one that holds a file. The call is recorded.
        """
        self.calls.append(("is_dir", path))
        return any(path in key.parents for key in self.files)

    def is_file(self, path: Path) -> bool:
        """Tell whether a file or a directory that holds one is stored.

        Args:
            path: Any path.

        Returns:
            True when the path is a key.
        """
        return self.exists(path)

    def is_symlink(self, path: Path) -> bool:
        """Tell whether a path was given as a symbolic link.

        Args:
            path: Any path.

        Returns:
            True when the path is in `links`.
        """
        return path in self.links

    def list_dir(self, path: Path) -> Sequence[Path]:
        """List the stored files and the directories directly under a path.

        Args:
            path: The directory.

        Returns:
            The files whose parent is the path and the child of the path that
            holds each deeper file, sorted and without repeats. The call is
            recorded.
        """
        self.calls.append(("list_dir", path))
        found = {
            path / key.relative_to(path).parts[0]
            for key in self.files
            if path in key.parents
        }
        return sorted(found)


@dataclass
class FakeRepository:
    """A `Repository` whose root is fixed, or that is not inside a repository."""

    top: Path | None = ROOT
    message: str = "not inside a git repository: /elsewhere"

    identity_reads: int = 0
    identity_error: Exception | None = None

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

        Raises:
            Exception: The configured identity failure, if any.
            RuntimeError: The fake is outside any repository.
        """
        self.identity_reads += 1
        if self.identity_error is not None:
            raise self.identity_error
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


@dataclass
class FakeClock:
    """A clock with a fixed time or a configured failure.

    Attributes:
        seconds: Seconds since the epoch, or the exception to raise.
        reads: Number of time queries.
    """

    seconds: float | Exception
    reads: int = 0

    def now(self) -> float:
        """Read the configured time.

        Returns:
            The configured seconds since the epoch.

        Raises:
            Exception: The configured failure, if any.
        """
        self.reads += 1
        return value_or_raise(self.seconds)


@dataclass
class FakeDirectories:
    """Fixed directories for tests that need the Wio home or a temporary path.

    Attributes:
        home: The Wio home, or the exception to raise.
        temporary: The temporary directory.
        reads: The directory queries in order.
    """

    home: Path | Exception
    temporary: Path = Path("/tmp")
    reads: list[str] = field(default_factory=list)

    def wio_home(self) -> Path:
        """Read the configured Wio home.

        Returns:
            The fixed Wio home.

        Raises:
            Exception: The configured failure, if any.
        """
        self.reads.append("wio_home")
        return value_or_raise(self.home)

    def temp_dir(self) -> Path:
        """Read the configured temporary directory.

        Returns:
            The fixed temporary directory.
        """
        self.reads.append("temp_dir")
        return self.temporary


@dataclass
class FakeStdio:
    """In-memory standard streams that satisfy the `Stdio` port."""

    stdin: TextIO = field(default_factory=io.StringIO)
    stdout: TextIO = field(default_factory=io.StringIO)
    stderr: TextIO = field(default_factory=io.StringIO)


@dataclass
class FakeEntropy:
    """An `Entropy` that gives prepared bytes, the last again after them.

    Attributes:
        calls: The bytes of each call, in order.
        counts: How many bytes each call asked for, in order.
    """

    calls: Sequence[bytes] = (bytes([19, 3, 20, 9, 29, 23]),)
    counts: list[int] = field(default_factory=list)

    def random_bytes(self, count: int) -> bytes:
        """Give the next prepared bytes.

        Args:
            count: How many bytes were asked for.

        Returns:
            The next call's bytes, or the last when none is left.
        """
        self.counts.append(count)
        return self.calls[min(len(self.counts), len(self.calls)) - 1]


@dataclass
class RecordingSink:
    """An `EventSink` that keeps the events it is given.

    Attributes:
        events: The events written, in order.
        warning: What a write reports on `stderr` and still does not raise, or
            `None` for a sink that writes.
        stderr: Where the warning is reported.
    """

    events: list[Event] = field(default_factory=list)
    warning: str | None = None
    stderr: TextIO = field(default_factory=io.StringIO)

    def write(self, event: Event) -> None:
        """Keep the event, or report that the write failed.

        Args:
            event: The event to record.
        """
        if self.warning is None:
            self.events.append(event)
        else:
            self.stderr.write(f"warning: {self.warning}\n")


@dataclass(frozen=True)
class FakeRules:
    """A `StageRules` port over a table of the rules of each stage of a Work.

    Attributes:
        rules: For a Work, an action and a stage, the qualified code of each rule
            it selects with its hash; a stage that is not a key selects none.
    """

    rules: Mapping[tuple[str, str, str], Mapping[str, str]] = field(
        default_factory=dict
    )

    def selected(self, work_id: str, action: str, stage: str) -> Mapping[str, str]:
        """Give the rules that a stage of a Work selects.

        Args:
            work_id: The Work's id.
            action: The action.
            stage: The stage.

        Returns:
            The rules of the table for it, or none.
        """
        return self.rules.get((work_id, action, stage), {})


@dataclass(frozen=True)
class FakeFirstParents:
    """A `History` port over a line of commits, which gives them newest first.

    Attributes:
        commits: The commits from the oldest.
    """

    commits: tuple[Commit, ...]

    def first_parents(self, revision: str) -> tuple[Commit, ...]:
        """List the commits, newest first.

        Args:
            revision: The revision, which must be `HEAD`.

        Returns:
            The commits from `HEAD` down.
        """
        assert revision == "HEAD"
        return tuple(reversed(self.commits))
