# SPDX-License-Identifier: Apache-2.0
"""The real adapters of the ports of `wio.io`."""

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from wio.models.commits import Commit

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import TextIO

    from wio.env.ports import Environment


class SystemStdio:
    """The process's own standard streams, as the `Stdio` port.

    Once built, its `stdin`, `stdout` and `stderr` are the streams of `sys`.
    """

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO

    def __init__(self) -> None:
        """Bind the streams of `sys`."""
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr


class LocalFileSystem:
    """The local disk, as the `FileSystem` port.

    Paths are absolute or relative to the working directory, and a failure to
    reach a file raises the `OSError` subclass that describes it.
    """

    def read_text(self, path: Path) -> str:
        """Read a file as UTF-8 text.

        Args:
            path: The file to read.

        Returns:
            The file's content, with its line ends as stored.

        Raises:
            FileNotFoundError: If the file does not exist.
            UnicodeDecodeError: If the file is not valid UTF-8.
        """
        return path.read_bytes().decode("utf-8")

    def resolve(self, path: Path) -> Path:
        """Resolve a local path, including a path that does not yet exist.

        Args:
            path: The path to resolve.

        Returns:
            The absolute path with symbolic links followed.
        """
        return path.resolve()

    def read_bytes(self, path: Path) -> bytes:
        """Read a file as it is stored.

        Args:
            path: The file to read.

        Returns:
            The file's bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        return path.read_bytes()

    def write_text(self, path: Path, text: str) -> None:
        """Write a file as UTF-8 text, creating its parent directories.

        Args:
            path: The file to write.
            text: The content, written exactly as given.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def append_text(self, path: Path, text: str) -> None:
        """Append UTF-8 text to a file in one write, creating it if needed.

        Args:
            path: The file to append to, whose parents are created.
            text: The content, appended exactly as given.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as stream:
            stream.write(text.encode("utf-8"))

    def exists(self, path: Path) -> bool:
        """Tell whether a path exists.

        Args:
            path: A file or directory.

        Returns:
            True when the path exists.
        """
        return path.exists()

    def is_dir(self, path: Path) -> bool:
        """Tell whether a path is a directory.

        Args:
            path: Any path.

        Returns:
            True when the path exists and is a directory.
        """
        return path.is_dir()

    def is_file(self, path: Path) -> bool:
        """Tell whether a path is a regular file.

        Args:
            path: Any path.

        Returns:
            True when the path exists and is a regular file.
        """
        return path.is_file()

    def is_symlink(self, path: Path) -> bool:
        """Tell whether a path is a symbolic link, whatever it points to.

        Args:
            path: Any path.

        Returns:
            True when the path is a symbolic link, also one that is broken.
        """
        return path.is_symlink()

    def list_dir(self, path: Path) -> Sequence[Path]:
        """List a directory's entries.

        Args:
            path: The directory.

        Returns:
            The entries sorted by name, so the listing never depends on the
            order the disk returns.

        Raises:
            FileNotFoundError: If the path does not exist.
            NotADirectoryError: If the path is not a directory.
        """
        return sorted(path.iterdir(), key=lambda entry: entry.name)


_NEXT = "run wio from a directory inside the repository"


def _check_directory(directory: Path) -> None:
    """Check that the directory git is to run in exists and can be entered.

    Args:
        directory: The working directory the environment reported.

    Raises:
        RuntimeError: If it does not exist, is not a directory or cannot be
            entered. The message names it, says which, and says to run wio
            from inside the repository.
    """
    if not directory.exists():
        message = f"the working directory {directory} does not exist; {_NEXT}"
        raise RuntimeError(message)
    if not directory.is_dir():
        message = f"the working directory {directory} is not a directory; {_NEXT}"
        raise RuntimeError(message)
    if not os.access(directory, os.X_OK):
        message = f"the working directory {directory} cannot be entered; {_NEXT}"
        raise RuntimeError(message)


def _run_git(
    environment: Environment, arguments: Sequence[str]
) -> subprocess.CompletedProcess[str]:
    """Run git in the environment's working directory.

    Args:
        environment: Reports the working directory git runs in.
        arguments: The arguments after `git`.

    Returns:
        The completed process, whatever its exit code, with its output decoded
        as UTF-8 and its line endings left as git printed them, so a CRLF in a
        file or a message is not turned into an LF.

    Raises:
        RuntimeError: If the working directory does not exist, is not a
            directory or cannot be entered, or git cannot be run. The message
            says what is wrong and what to do, and names the working directory
            the environment reported, except when git cannot be run.
        UnicodeDecodeError: If what git printed is not UTF-8 text.
    """
    directory = environment.working_directory()
    _check_directory(directory)
    try:
        done = subprocess.run(
            ["git", *arguments], cwd=directory, capture_output=True, check=False
        )
    except OSError as error:
        reason = error.strerror or str(error)
        message = f"cannot run git: {reason}; check that git is installed and on PATH"
        raise RuntimeError(message) from error
    return subprocess.CompletedProcess(
        done.args,
        done.returncode,
        done.stdout.decode("utf-8"),
        done.stderr.decode("utf-8", errors="replace"),
    )


def _git_path(environment: Environment, *arguments: str) -> Path:
    """Run `git rev-parse` in the environment's directory and read its path.

    Args:
        environment: Reports the working directory git runs in.
        *arguments: The options after `git rev-parse`.

    Returns:
        The path git printed.

    Raises:
        RuntimeError: If the working directory does not exist, is not a
            directory or is not inside a repository, or git cannot be run. Each
            message says what is wrong and what to do, and names the working
            directory the environment reported, except when git cannot be run.
    """
    done = _run_git(environment, ["rev-parse", *arguments])
    if done.returncode != 0:
        directory = environment.working_directory()
        message = (
            f"not inside a git repository (working directory {directory}); {_NEXT}"
        )
        raise RuntimeError(message)
    return Path(done.stdout.strip())


class _InWorkingDirectory:
    """What the git adapters share: where the working directory comes from."""

    def __init__(self, environment: Environment) -> None:
        """Keep the environment that tells where the working directory is.

        Args:
            environment: Reports the working directory git runs in.
        """
        self._environment: Environment = environment


class GitRepository(_InWorkingDirectory):
    """The repository of the working directory, read with git, as `Repository`.

    `root` and `identity` ask git, which must be installed wherever wio runs
    because the `git` trailer reader needs it too. A missing git, a working
    directory that does not exist, is not a directory or cannot be entered, and
    a directory outside a repository each raise a `RuntimeError` that says which
    and what to do, and names the working directory except when git cannot be
    run.

    It is given an `Environment` and runs git in the working directory that the
    environment reports, never in one it finds itself, so a test can fix it.
    """

    def root(self) -> Path:
        """Find the top of the working tree.

        Returns:
            The absolute path of the repository root.
        """
        return _git_path(self._environment, "--show-toplevel")

    def identity(self) -> Path:
        """Find the path that identifies the clone.

        Returns:
            The absolute path of the git directory that every worktree of one
            clone shares.
        """
        return _git_path(
            self._environment, "--path-format=absolute", "--git-common-dir"
        )

    def show_index(self, path: Path) -> str | None:
        """Read a file as it is staged in the index.

        It changes nothing: the index, the refs and the working tree are the
        same after the call.

        Args:
            path: The file, relative to the repository root, whatever the
                working directory inside the repository is.

        Returns:
            The staged content, or `None` when the index has no such file.

        Raises:
            RuntimeError: If the working directory is not inside a repository,
                as the other members do.
            ValueError: If the staged content is not UTF-8 text.
        """
        return _content(self._environment, f":{path.as_posix()}")

    def is_dirty(self) -> bool:
        """Tell whether the working tree has uncommitted changes.

        It takes no optional lock and writes nothing, such as the index that a
        plain `git status` refreshes, so a read leaves the repository as it was.

        Returns:
            True when a tracked file differs from `HEAD` or the index, or when
            an untracked file that is not ignored exists.

        Raises:
            RuntimeError: If the working directory is not inside a repository,
                as the other members do.
        """
        status = _git_text(
            self._environment,
            "--no-optional-locks",
            "status",
            "--porcelain",
            "--untracked-files=normal",
        )
        return bool(status)


class GitHistory(_InWorkingDirectory):
    """The revisions of the working directory's repository, as `History`.

    It is given an `Environment` and runs git in the working directory that the
    environment reports, as `GitRepository` does, and raises the same
    `RuntimeError` for a directory that is not usable, outside a repository, or
    when git cannot be run. A revision or range that git rejects raises
    `ValueError` that names it. Every read leaves the repository as it was.
    """

    def rev_parse(self, revision: str) -> str:
        """Resolve a revision to a full commit id.

        Args:
            revision: A revision such as `HEAD`.

        Returns:
            The full 40-character id.

        Raises:
            ValueError: If git rejects the revision.
        """
        return _git_text(
            self._environment,
            "rev-parse",
            "--verify",
            "--end-of-options",
            f"{revision}^{{commit}}",
        )

    def history(self, revision_range: str) -> Sequence[Commit]:
        """List the commits of a revision range.

        Args:
            revision_range: A range such as `main..HEAD`.

        Returns:
            The commits oldest first, parents before children, a merge commit
            included, each with its full id and its message as committed,
            without its trailing newline; none for an empty range.

        Raises:
            ValueError: If git rejects the range.
        """
        return _commits(self._environment, revision_range, "--topo-order", "--reverse")

    def first_parents(self, revision: str) -> Sequence[Commit]:
        """List a revision's ancestors along first parents.

        Args:
            revision: The revision to start from, such as `HEAD`.

        Returns:
            The commits newest first, starting with the revision's own; the
            commits that a merge brought in are not in it.

        Raises:
            ValueError: If git rejects the revision.
        """
        return _commits(self._environment, revision, "--first-parent")

    def list_files(self, revision: str) -> Sequence[Path]:
        """List the files of a revision's tree.

        Args:
            revision: The revision, such as `HEAD`.

        Returns:
            The paths relative to the repository root, whatever the working
            directory inside the repository is, sorted by path.

        Raises:
            ValueError: If git rejects the revision.
        """
        return _paths(self._environment, revision)

    def show(self, revision: str, path: Path) -> str | None:
        """Read a file as it was at a revision.

        Args:
            revision: The revision, such as `HEAD`.
            path: The file, relative to the repository root.

        Returns:
            The file's content, or `None` when it did not exist then.

        Raises:
            ValueError: If git rejects the revision.
        """
        return _blob(self._environment, revision, path)


def _git_text(environment: Environment, *arguments: str) -> str:
    """Run git in the environment's working directory and read its output.

    Args:
        environment: Reports the working directory git runs in.
        *arguments: The arguments after `git`.

    Returns:
        What git printed, without its trailing newline.

    Raises:
        RuntimeError: If the working directory is not usable or not inside a
            repository, or git cannot be run, as `GitRepository` says.
        ValueError: If git rejects a revision or range among the arguments. The
            message is git's own followed by the command, so it names them.
    """
    _git_path(environment, "--git-dir")
    done = _run_git(environment, arguments)
    if done.returncode != 0:
        reason = done.stderr.strip() or "git failed"
        message = f"{reason} (git {' '.join(arguments)})"
        raise ValueError(message)
    return done.stdout.removesuffix("\n")


def _commits(environment: Environment, revision: str, *options: str) -> list[Commit]:
    """Read the commits that `git log` lists for a revision or range.

    Args:
        environment: Reports the working directory git runs in.
        revision: The revision or range.
        *options: The `git log` options that choose the order.

    Returns:
        The commits in the order git printed them, each with its full id and its
        message without the trailing newline.

    Raises:
        RuntimeError: As `_git_text`.
        ValueError: As `_git_text`.
    """
    out = _git_text(
        environment,
        "log",
        "-z",
        "--format=%H%x00%B",
        *options,
        "--end-of-options",
        revision,
    )
    fields = [field.removesuffix("\n") for field in out.split("\0")]
    return [Commit(fields[i], fields[i + 1]) for i in range(0, len(fields) - 1, 2)]


def _paths(environment: Environment, revision: str) -> list[Path]:
    """List the files of a revision's tree.

    Args:
        environment: Reports the working directory git runs in.
        revision: The revision.

    Returns:
        The paths relative to the repository root, sorted by path.

    Raises:
        RuntimeError: As `_git_text`.
        ValueError: As `_git_text`.
    """
    out = _git_text(
        environment,
        "ls-tree",
        "-r",
        "--name-only",
        "-z",
        "--full-tree",
        "--end-of-options",
        revision,
    )
    return sorted(Path(name) for name in out.split("\0") if name)


def _blob(environment: Environment, revision: str, path: Path) -> str | None:
    """Read a file as it was at a revision.

    Args:
        environment: Reports the working directory git runs in.
        revision: The revision.
        path: The file, relative to the repository root.

    Returns:
        The content, or `None` when the revision has no such file.

    Raises:
        RuntimeError: As `_git_text`.
        ValueError: As `_git_text`, and if the content is not UTF-8 text.
    """
    _git_text(
        environment,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{revision}^{{commit}}",
    )
    return _content(environment, f"{revision}:{path.as_posix()}")


def _content(environment: Environment, spec: str) -> str | None:
    """Read the object a `revision:path` or `:path` specification names.

    Args:
        environment: Reports the working directory git runs in.
        spec: A specification such as `HEAD:a.txt`, or `:a.txt` for the index,
            whose path is relative to the repository root.

    Returns:
        The content exactly as git stores it, or `None` when git finds no such
        file, a directory included.

    Raises:
        RuntimeError: As `_git_text`.
        ValueError: If the content is not UTF-8 text.
    """
    _git_path(environment, "--git-dir")
    done = _run_git(environment, ["cat-file", "blob", spec])
    return done.stdout if done.returncode == 0 else None
